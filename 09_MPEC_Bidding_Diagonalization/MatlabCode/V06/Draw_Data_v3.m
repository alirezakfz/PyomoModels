currentFolder = pwd
TestSystemXLFile = [currentFolder,'\',DatasetList{DatasetSelection},'\',TestSystemList{TestSystemSelection}];
TestSystemXLFile = [currentFolder,'\',DatasetList{DatasetSelection},'\',TestSystemList{TestSystemSelection}];
SDAOffersXLFile =  [currentFolder,'\',DatasetList{DatasetSelection},'\Strategic DA Quantity Offers.xlsx'];
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  Transmission Grid %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%  Grid Structure
% Number of Buses
n = xlsread(TestSystemXLFile,'Structure','A2');

% Number of Lines
nl = xlsread(TestSystemXLFile,'Structure','B2');

% Number of Generators
ng = xlsread(TestSystemXLFile,'Structure','C2');

% Number of Competitive DAs
ncda = xlsread(TestSystemXLFile,'Structure','D2');

% Number of Strategic DAs
nsda = xlsread(TestSystemXLFile,'Structure','E2');

% Number Of DAs
nda = ncda+nsda;

%% Create Data
if RandomOrExcel=='R'
    Create_Data_v0
end
%%


% GenLoc defines the position (bus index) of each generator
LastRow = sprintf('%d',2+ng-1);
GenBus = xlsread(TestSystemXLFile,'Generators',strcat('B2:B',LastRow));
GenLoc = zeros(n,ng);
for gg = 1:ng
    GenLoc(GenBus(gg),gg) = 1;
end

% CDALoc defines the position (bus index) of each FSP's load
LastRow = sprintf('%d',2+ncda-1);
CDABus = xlsread(TestSystemXLFile,'CDA Price Offers_Bids',strcat('A2:A',LastRow));
% CDALoc = zeros(n,ncda);
% for dd=1:ncda
%     CDALoc(CDABus(dd),dd) = 1;
% end

% SDALoc defines the position (bus index) of each Strategic DA
LastRow = sprintf('%d',2+nsda-1);
SDABus = xlsread(TestSystemXLFile,'Structure',strcat('F2:F',LastRow));
DABus = [CDABus;SDABus];
DALoc = zeros(n,nda);
for mg=1:nda
    DALoc(DABus(mg),mg) = 1;
end

% Power Lines Susceptance
LastRow = sprintf('%d',2+nl-1);
LinesSusc = transpose(xlsread(TestSystemXLFile,'Lines',strcat('E2:E',LastRow)));

% Source Buses
FromBus = xlsread(TestSystemXLFile,'Lines',strcat('B2:B',LastRow));
% Destination Buses
ToBus = xlsread(TestSystemXLFile,'Lines',strcat('C2:C',LastRow));

% Susceptance Matrix and LineFlows Matrix
% LineFlows indicates the starting and ending nodes of each line
B = zeros(n);
LineFlows = zeros(nl,n);
for kk=1:nl
    % Off Diagonal elements of B Matrix
    B(FromBus(kk),ToBus(kk)) = -LinesSusc(kk);
    B(ToBus(kk),FromBus(kk)) = B(FromBus(kk),ToBus(kk));
    % LineFlows Matrix
    LineFlows(kk,FromBus(kk)) = 1;
    LineFlows(kk,ToBus(kk)) = -1;
end
% Diagonal Elements of B Matrix
for ii=1:n
    B(ii,ii) = -sum(B(ii,:));
end

% Power Lines' Capacities
LastRow = sprintf('%d',2+nl-1);
FMAX = (xlsread(TestSystemXLFile,'Lines',strcat('F2:F',LastRow))./MVA).*gen_multiplier;

%% Thermal Generators
LastRow = sprintf('%d',2+ng-1);
% Generators' Price Offers
GenBidsPerTimeslot = xlsread(TestSystemXLFile,'Generators',strcat('H2:','H',LastRow));
GenBids = GenBidsPerTimeslot*ones(1,T);
% % % % GenBids = -5*rand(1,24)+GenBidsPerTimeslot+5*rand(1,24);
% Generators' Production Lower Bounds
GMINPerTimeslot = xlsread(TestSystemXLFile,'Generators',strcat('D2:D',LastRow))./MVA;
GMIN = (GMINPerTimeslot*ones(1,T)).*gen_multiplier;

% Generators' Production Upper Bounds
GMAXPerTimeslot = xlsread(TestSystemXLFile,'Generators',strcat('C2:C',LastRow))./MVA;
GMAX = (GMAXPerTimeslot*ones(1,T)).*gen_multiplier;

%% Strategic DA Price Offers
LastRow = sprintf('%d',2+nsda-1);
sda_price_offers = xlsread(TestSystemXLFile,'SDA Price Offers_Bids',strcat('C2:Z',LastRow));
sda_price_bids = xlsread(TestSystemXLFile,'SDA Price Offers_Bids',strcat('AB2:AY',LastRow));

%% Strategic DA Quantity Offers/Bids
LastRow = sprintf('%d',2+nsda-1);

sda_quantity_offers = (xlsread(SDAOffersXLFile,'Offers',strcat('B2:Y',LastRow))./MVA);
%sda_quantity_offers = (xlsread(SDAOffersXLFile,'Offers',strcat('B2:Y',LastRow)));

sda_quantity_bids = (xlsread(SDAOffersXLFile,'Bids',strcat('B2:Y',LastRow))./MVA).*gen_multiplier;
%sda_quantity_bids = (xlsread(SDAOffersXLFile,'Bids',strcat('B2:Y',LastRow))).*gen_multiplier;

%% Competitive DA Price Offers/Bids
LastRow = sprintf('%d',2+ncda-1);
cda_price_offers = xlsread(TestSystemXLFile,'CDA Price Offers_Bids',strcat(('C2:Z'),LastRow));
cda_price_bids = xlsread(TestSystemXLFile,'CDA Price Offers_Bids',strcat(('AB2:AY'),LastRow));

%% Competitive DA Quantity Offers/Bids
LastRow = sprintf('%d',2+ncda-1);

%cda_quantity_offers = (xlsread(TestSystemXLFile,'CDA Quantity Offers_Bids',strcat(('C2:Z'),LastRow))./MVA).*dem_multiplier;
cda_quantity_offers = (xlsread(TestSystemXLFile,'CDA Quantity Offers_Bids',strcat(('C2:Z'),LastRow)));

%cda_quantity_bids = (xlsread(TestSystemXLFile,'CDA Quantity Offers_Bids',strcat(('AB2:AY'),LastRow))./MVA).*dem_multiplier;
cda_quantity_bids = (xlsread(TestSystemXLFile,'CDA Quantity Offers_Bids',strcat(('AB2:AY'),LastRow)));

if RandomOrExcel=='E'
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  Prosumers %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% EVs
    % Max SOE
    
    %EV_SOC_max = (xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\EVs.xlsx'],'max_soc',xlRC2A1(2,2,Large_Random_Number+1,2+nsda-1)))/MVA;
    EV_SOC_max = ((xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\EVs.xlsx'],'max_soc',xlRC2A1(2,2,Large_Random_Number+1,2+nsda-1)))/MVA).*dem_multiplier;
    
    EV_SOC_max(isnan(EV_SOC_max)) = 0;
    % Number Of EVs per Strategic DA
    nev = zeros(1,nsda);
    for ii=1:nsda
        nev(ii) = sum(EV_SOC_max(:,ii)>0);
    end
    % Min SOE
    %EV_SOC_min = (xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\EVs.xlsx'],'min_soc',xlRC2A1(2,2,max(nev)+1,2+nsda-1)))/MVA;
    EV_SOC_min = ((xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\EVs.xlsx'],'min_soc',xlRC2A1(2,2,max(nev)+1,2+nsda-1)))/MVA).*dem_multiplier;
    EV_SOC_min(isnan(EV_SOC_min)) = 0;
    
    % Charging Rate
    %EV_power_max = (xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Charging Power',xlRC2A1(2,2,max(nev)+1,2+nsda-1)))/MVA;
    EV_power_max = ((xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Charging Power',xlRC2A1(2,2,max(nev)+1,2+nsda-1)))/MVA).*dem_multiplier;
    EV_power_max(isnan(EV_power_max)) = 0;
    
    % Arrival Times
    %EV_Arrivals = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Arrival Times',xlRC2A1(2,2,max(nev)+1,2+nsda-1));
    EV_Arrivals = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Arrival Times',xlRC2A1(2,2,max(nev)+1,2+nsda-1))-15;
    EV_Arrivals(isnan(EV_Arrivals)) = 0;
    
    % Departure Times
    %EV_Departures = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Departure Times',xlRC2A1(2,2,max(nev)+1,2+nsda-1));
    EV_Departures = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Departure Times',xlRC2A1(2,2,max(nev)+1,2+nsda-1))-15;
    EV_Departures(isnan(EV_Departures)) = 0;
    
    % Initial SOE
    %EV_Initial_SOC = (xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Arrival SOC',xlRC2A1(2,2,max(nev)+1,2+nsda-1)))/MVA;
    EV_Initial_SOC = ((xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Arrival SOC',xlRC2A1(2,2,max(nev)+1,2+nsda-1)))/MVA).*dem_multiplier;%/MVA;
    EV_Initial_SOC(isnan(EV_Initial_SOC)) = 0;
    
    % Charging Efficiency
    %Charging_eff = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Charging Efficiency',xlRC2A1(2,2,max(nev)+1,2+nsda-1));
    Charging_eff = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Charging Efficiency',xlRC2A1(2,2,max(nev)+1,2+nsda-1));
    Charging_eff(isnan(Charging_eff)) = 0;
    
    % Discharging Efficiency
    %Discharging_eff = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Discharging Efficiency',xlRC2A1(2,2,max(nev)+1,2+nsda-1));
    Discharging_eff = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\EVs.xlsx'],'Discharging Efficiency',xlRC2A1(2,2,max(nev)+1,2+nsda-1));
    Discharging_eff(isnan(Discharging_eff)) = 0;
    %% TCLs
    % Max Consumption
    %TCL_max = (xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Max Consumption',xlRC2A1(2,2,Large_Random_Number+1,2+nsda-1)))/MVA;
    TCL_max = (xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Max Consumption',xlRC2A1(2,2,Large_Random_Number+1,2+nsda-1)))/MVA;
    TCL_max(isnan(TCL_max)) = 0;
    % Number Of TCLs per Strategic DA
    ntcl = zeros(1,nsda);
    for ii=1:nsda
        ntcl(ii) = sum(TCL_max(:,ii)>0);
    end
    % Beta
    %TCL_beta = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Beta',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_beta = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Beta',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_beta(isnan(TCL_beta)) = 0;
    % R
    %TCL_R = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\TCL.xlsx'],'R',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_R = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\TCL.xlsx'],'R',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_R(isnan(TCL_R)) = 0;
    % Low Temps
    %TCL_temp_low = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Low Temps',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_temp_low = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Low Temps',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_temp_low(isnan(TCL_temp_low)) = 0;
    % Outside Temperature
    %outside_temp = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Outside Temperature','B2:Y2');
    outside_temp = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Outside Temperature','B2:Y2');
    % Start Times
    %TCL_start = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Start Times',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_start = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Start Times',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1))-15;
    TCL_start(isnan(TCL_start)) = 0;
    % End Times
    %TCL_end = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\TCL.xlsx'],'End Times',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_end = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\TCL.xlsx'],'End Times',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1))-15;
    TCL_end(isnan(TCL_end)) = 0;
    % COP
    %TCL_COP = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\TCL.xlsx'],'COP',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_COP = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\TCL.xlsx'],'COP',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_COP(isnan(TCL_COP)) = 0;
    % High Temp
    TCL_temp_high = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\TCL.xlsx'],'Up Temps',xlRC2A1(2,2,max(ntcl)+1,2+nsda-1));
    TCL_temp_high(isnan(TCL_temp_high)) = 27;
    %% SLs
    % Start Times
    %SL_start = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\SL.xlsx'],'SL Start',xlRC2A1(2,2,Large_Random_Number+1,2+nsda-1));
    SL_start = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\SL.xlsx'],'SL Start',xlRC2A1(2,2,Large_Random_Number+1,2+nsda-1))-15;
    SL_start(isnan(SL_start)) = 0;
    
    % Number Of SLs per Strategic DA
    nsl = zeros(1,nsda);
    for ii=1:nsda
        nsl(ii) = sum(SL_start(:,ii)>0);
    end
    % End Times
    %SL_end = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\SL.xlsx'],'SL End',xlRC2A1(2,2,max(nsl)+1,2+nsda-1));
    SL_end = xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\SL.xlsx'],'SL End',xlRC2A1(2,2,max(nsl)+1,2+nsda-1))-15;
    SL_end(isnan(SL_end)) = 0;
    % SL profiles
    %SL_profile = xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\SL.xlsx'],'SL Consumption',xlRC2A1(3,2,max(nsl)+2,T*nsda+1))./(MVA);
    SL_profile = (xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\SL.xlsx'],'SL Consumption',xlRC2A1(2,2,max(nsl)+2,T*nsda+1))./MVA).*dem_multiplier;
    SL_profile(isnan(SL_profile)) = -1;
    % SL cycle
    SL_cycle = zeros(max(nsl),nsda);
    for ii=1:nsda
        for ss=1:max(nsl)
            SL_cycle_for_all_devices = sum(SL_profile(:,(ii-1)*T+1:ii*T)>=0,2);
            SL_cycle(ss,ii) = SL_cycle_for_all_devices(ss);
        end
    end
end
%% Inflexible Load
LastRow = sprintf('%d',2+nsda-1);
%InfLoad = (xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\Inflexible Consumption.xlsx'],'Sheet1',strcat('B2:Y',LastRow))./MVA).*dem_multiplier;
InfLoad = (xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\Inflexible Consumption.xlsx'],'Sheet1',strcat('B2:Y',LastRow))./MVA).*dem_multiplier;%./MVA);%.*dem_multiplier;
%DRBids = (xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\Inflexible Consumption.xlsx'],'Sheet2',strcat('B2:Y',LastRow)));
%DRBids = (xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\Inflexible Consumption.xlsx'],'Sheet2',strcat('B2:Y',LastRow)));
%% RES
%RES = (xlsread(['C:\Users\konster\OneDrive\Έγγραφα\Complementarity Models\EPEC-Learning paper\',DatasetList{DatasetSelection},'\Renewable Production.xlsx'],'Sheet1',strcat('B2:Y',LastRow))./MVA).*dem_multiplier;
RES = (xlsread([currentFolder,'\',DatasetList{DatasetSelection},'\Renewable Production.xlsx'],'Sheet1',strcat('B2:Y',LastRow))./MVA).*dem_multiplier;%./MVA);%.*dem_multiplier;