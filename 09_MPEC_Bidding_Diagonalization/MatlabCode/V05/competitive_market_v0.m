clear,clc,close all
% The rivals' bids are updated after each algorithm's round
RandomOrExcel = 'E';
CurtailableDemand = 0;
load_factor = 1;
gen_multiplier = 1;
dem_multiplier = 1;
prosumers_range = [100 100];
Large_Random_Number = 10000; 
e_tol = 0.0001;
e_tol_perc = 0.0001;

% Add an upper bound for indoors temperature or not?
temp_upper_bound = 0;

%% Input
% 'Ali Data':      1
% 'Konster Data':  2
DatasetList = {'Ali Data','Konster Data','Test Data','Test Data 2','Test Data 4','Test Data 5'};
DatasetSelection = 2;

% '6_Bus_Transmission_Test_System.xlsx'     1
TestSystemList = {'6_Bus_Transmission_Test_System.xlsx'};
TestSystemSelection = 1;
BIGF = 10000;
BIGM = 10000;
MVA = 30;
% npr = 500;
T = 24;
% Charge_eff = 0.94;
% Discharge_eff = 0.94;
RefBus = 1;

% c_DA_o = [13,12,14,15,14,13,15,14,14,15,14,15,14,12,15,12,12,14,13,12,12,12,13,13];
% c_DA_b = [102,104,101,98,75,108,72,97,90,108,86,71,75,84,106,107,71,87,106,72,81,100,103,98];

% Input Data
Draw_Data_v3

B(:,RefBus) = [];
Yline = (LineFlows'.*LinesSusc)';
Yline(:,RefBus) = [];

da_price_offers = zeros(nda,T);
da_price_bids = 150*ones(nda,T);

% Model
comp_market = optimproblem('ObjectiveSense','min');

% Variables
g = optimvar('g',ng,T,'LowerBound',0,'UpperBound',GMAX);
theta = optimvar('theta',n-1,T,'LowerBound',-pi,'UpperBound',pi);
ch = optimvar('ch',max(nev)*nda,T,'LowerBound',0);
dis = optimvar('dis',max(nev)*nda,T,'LowerBound',0);
soe = optimvar('soe',max(nev)*nda,T,'LowerBound',repmat(EV_SOC_min(:),1,T),'UpperBound',repmat(EV_SOC_max(:),1,T)); % (a.5)
u_ev = optimvar('u_ev',max(nev)*nda,T,'Type','integer','LowerBound',0,'UpperBound',1);
p_tcl = optimvar('p_tcl',max(ntcl)*nda,T,'LowerBound',0,'UpperBound',repmat(TCL_max(:),1,T));% (a.7)
tcl_temp = optimvar('tcl_temp',max(ntcl)*nda,T);
p_sl = optimvar('p_sl',max(nsl)*nda,T,'LowerBound',0);
w = optimvar('w',max(nsl)*nda,T,'Type','integer','LowerBound',0,'UpperBound',1);
p_res = optimvar('p_res',nda,T,'LowerBound',0,'UpperBound',RES); %WE ALLOW RES SPILLAGE!!!!!!!
if CurtailableDemand==1
    p_dr = optimvar('p_dr',nda,T,'LowerBound',0,'UpperBound',InfLoad); 
end
da_sell = optimvar('da_sell',nda,T,'LowerBound',0);
da_buy = optimvar('da_buy',nda,T,'LowerBound',0);
u_bigM = optimvar('u_bigM',nda,T,'Type','integer','LowerBound',0,'UpperBound',1);
% Constraints
TSOPowerBalance = optimexpr(n,T);
for tt=1:T
    TSOPowerBalance(:,tt) = -GenLoc*g(:,tt)-DALoc*(da_sell(:,tt)-da_buy(:,tt))+B*theta(:,tt);
end

comp_market.Constraints.power_balance = TSOPowerBalance==0;

comp_market.Constraints.upper_line_limit = Yline*theta<=FMAX*ones(1,T);
comp_market.Constraints.lower_line_limit = -Yline*theta<=FMAX*ones(1,T);

%%%%% EVs %%%%%%%%%%%%%%%%%%%%
a2 = optimconstr(max(nev)*nda,T);
ch_zero = optimconstr(max(nev)*nda,T);
a3 = optimconstr(max(nev)*nda,T);
dis_zero = optimconstr(max(nev)*nda,T);
a4t1 = optimconstr(max(nev)*nda,T);
a4t2 = optimconstr(max(nev)*nda,T);
a6 = optimconstr(1,max(nev));
a8 = optimconstr(max(ntcl),T);
a9l = optimconstr(max(ntcl),T);
if temp_upper_bound
    a9r = optimconstr(max(ntcl),T);
end
initial_temp = optimconstr(1,max(ntcl));
SL_bin_con = optimconstr(max(nsl),T);
a10 = optimconstr(max(nsl),T);

EV_Arrivals_vec = EV_Arrivals(:);
EV_Departures_vec = EV_Departures(:);
EV_power_max_vec = EV_power_max(:);
EV_SOC_max_vec = EV_SOC_max(:);
Charging_eff_vec = Charging_eff(:);
Discharging_eff_vec = Discharging_eff(:);
TCL_start_vec = TCL_start(:);
TCL_end_vec = TCL_end(:);
TCL_beta_vec = TCL_beta(:);
TCL_COP_vec = TCL_COP(:);
TCL_R_vec = TCL_R(:);
TCL_temp_low_vec = TCL_temp_low(:);
if temp_upper_bound
    TCL_temp_high_vec = TCL_temp_high(:);
end
SL_start_vec = SL_start(:);
SL_end_vec = SL_end(:);
SL_cycle_vec = SL_cycle(:);


SL_profile_vec = zeros(max(nsl)*ii,T);
for ii=1:nda
    if ii==1
        SL_profile_vec(1:ii*max(nsl),:) = SL_profile(:,1:T);
    elseif ii>1
        SL_profile_vec((ii-1)*max(nsl)+1:ii*max(nsl),:) = SL_profile(:,(ii-1)*T+1:ii*T);
    end
end

SL_profile_vec(SL_profile_vec<0) = 0;

for ii=1:max([nev,ntcl,nsl])*nda
    if ii<=max(nev)*nda
        if EV_Arrivals_vec(ii)>0
            a2(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii)) = ch(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii))<=(u_ev(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii)).*repmat(EV_power_max_vec(ii),1,EV_Departures_vec(ii)-EV_Arrivals_vec(ii)+1));
            ch_zero(ii,[1:EV_Arrivals_vec(ii)-1,EV_Departures_vec(ii)+1:end]) = ch(ii,[1:EV_Arrivals_vec(ii)-1,EV_Departures_vec(ii)+1:end])==0;
            a3(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii))=dis(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii))<=(1-u_ev(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii))).*repmat(EV_power_max_vec(ii),1,EV_Departures_vec(ii)-EV_Arrivals_vec(ii)+1);
            dis_zero(ii,[1:EV_Arrivals_vec(ii)-1,EV_Departures_vec(ii)+1:end]) = dis(ii,[1:EV_Arrivals_vec(ii)-1,EV_Departures_vec(ii)+1:end])==0;
            a4t1(ii,EV_Arrivals_vec(ii)) = soe(ii,EV_Arrivals_vec(ii)) == EV_Initial_SOC(ii)+ch(ii,EV_Arrivals_vec(ii)).*Charging_eff_vec(ii)-dis(ii,EV_Arrivals_vec(ii))./Discharging_eff_vec(ii);
            a4t2(ii,EV_Arrivals_vec(ii)+1:EV_Departures_vec(ii)) = soe(ii,EV_Arrivals_vec(ii)+1:EV_Departures_vec(ii)) == soe(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii)-1)+ch(ii,EV_Arrivals_vec(ii)+1:EV_Departures_vec(ii)).*repmat(Charging_eff_vec(ii),1,EV_Departures_vec(ii)-EV_Arrivals_vec(ii))-dis(ii,EV_Arrivals_vec(ii)+1:EV_Departures_vec(ii))./repmat(Discharging_eff_vec(ii),1,EV_Departures_vec(ii)-EV_Arrivals_vec(ii));
            a6(ii) = soe(ii,EV_Departures_vec(ii)) == EV_SOC_max_vec(ii);
        else
            ch_zero(ii,:) = ch(ii,:)==0;
            dis_zero(ii,:) = dis(ii,:)==0;
        end
    end
    if ii<=max(ntcl)*nda
        if TCL_start_vec(ii)>0
            a8(ii,TCL_start_vec(ii)+1:TCL_end_vec(ii)) = tcl_temp(ii,TCL_start_vec(ii)+1:TCL_end_vec(ii)) ==  TCL_beta_vec(ii)*tcl_temp(ii,TCL_start_vec(ii):TCL_end_vec(ii)-1)+(1-TCL_beta_vec(ii))*(outside_temp(TCL_start_vec(ii):TCL_end_vec(ii)-1)+TCL_COP_vec(ii)*TCL_R_vec(ii)*(MVA*1000*p_tcl(ii,TCL_start_vec(ii):TCL_end_vec(ii)-1)));
            a9l(ii,TCL_start_vec(ii):TCL_end_vec(ii)) = tcl_temp(ii,TCL_start_vec(ii):TCL_end_vec(ii))>=TCL_temp_low_vec(ii);
            if temp_upper_bound
                a9r(ii,TCL_start_vec(ii):TCL_end_vec(ii)) = tcl_temp(ii,TCL_start_vec(ii):TCL_end_vec(ii))<=TCL_temp_high_vec(ii);
            end
            initial_temp(ii) = tcl_temp(ii,TCL_start_vec(ii)) == TCL_temp_low_vec(ii);
        end
    end
    
    if ii<=max(nsl)*nda
        if SL_start_vec(ii)>0
            SL_bin_con(ii,[1:SL_start_vec(ii)-1,SL_end_vec(ii):end]) = w(ii,[1:SL_start_vec(ii)-1,SL_end_vec(ii):end])==0;
            for tt=1:T
                if tt>=SL_start_vec(ii)&&tt<=SL_end_vec(ii)
                    if tt-SL_cycle_vec(ii)<0 % <= or <
                        a10(ii,tt) = p_sl(ii,tt) == w(ii,1:tt)*SL_profile_vec(ii,1:tt)';
                    else
                        a10(ii,tt) = p_sl(ii,tt) == w(ii,tt-[0:SL_cycle_vec(ii)-1])*SL_profile_vec(ii,1:SL_cycle_vec(ii))';
                    end
                else
                    a10(ii,tt) = p_sl(ii,tt) == 0;
                end
            end
        else
            a10(ii,:) = p_sl(ii,:) == 0;
        end
    end
end
comp_market.Constraints.charge_power_limit = a2;
comp_market.Constraints.charge_power_limit_zero = ch_zero;
comp_market.Constraints.discharge_power_limit = a3;
comp_market.Constraints.discharge_power_limit_zero = dis_zero;
comp_market.Constraints.soet1 = a4t1;
comp_market.Constraints.soet2 = a4t2;
comp_market.Constraints.soe_last_timeslot = a6;
comp_market.Constraints.tcl1 = a8;
comp_market.Constraints.tcl2 = a9l;
if temp_upper_bound
    comp_market.Constraints.tcl4 = a9r;
end
comp_market.Constraints.tcl3 = initial_temp;
comp_market.Constraints.sl1 = SL_bin_con;
comp_market.Constraints.sl2 = a10;
comp_market.Constraints.sl3 = sum(w,2)==1;


sum_ch = optimexpr(nda,T);
sum_dis = optimexpr(nda,T);
sum_ptcl = optimexpr(nda,T);
sum_psl = optimexpr(nda,T);
for jj=1:nda
    if jj==1
        sum_ch(jj,:) = sum(ch(1:max(nev),:));
        sum_dis(jj,:) = sum(dis(1:max(nev),:));
        sum_ptcl(jj,:) = sum(p_tcl(1:max(ntcl),:));
        sum_psl(jj,:) = sum(p_sl(1:max(nsl),:));
    elseif jj>1
        sum_ch(jj,:) = sum(ch((jj-1)*max(nev)+1:jj*max(nev),:));
        sum_dis(jj,:) = sum(dis((jj-1)*max(nev)+1:jj*max(nev),:));
        sum_ptcl(jj,:) = sum(p_tcl((jj-1)*max(ntcl)+1:jj*max(ntcl),:));
        sum_psl(jj,:) = sum(p_sl((jj-1)*max(nsl)+1:jj*max(nsl),:));
    end
end
comp_market.Constraints.DA_portfolio_balance = da_buy-da_sell == InfLoad-p_res+sum_ch-sum_dis+sum_ptcl+sum_psl;

comp_market.Constraints.offer_bigM1 = da_sell<=10000*u_bigM;
comp_market.Constraints.offer_bigM2 = da_buy<=10000*(1-u_bigM);

% Objective
comp_market.Objective = sum(sum(GenBids.*g))+sum(sum(da_price_offers.*da_sell))-sum(sum(da_price_bids.*da_buy));

%% Solver
[x_opt,Cost,output,exitflag] = solve(comp_market);
%[x_opt,Cost,output,exitflag]=gurobi(comp_market);
%results = gurobi(comp_market);

%% Extract LMPs %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Model
lin_comp_market = optimproblem('ObjectiveSense','min');

% Relax Integrality Constraints
lin_u_ev = optimvar('lin_u_ev',max(nev)*nda,T,'LowerBound',0,'UpperBound',1);
lin_w = optimvar('lin_w',max(nsl)*nda,T,'LowerBound',0,'UpperBound',1);
lin_u_bigM = optimvar('lin_u_bigM',nda,T,'LowerBound',0,'UpperBound',1);

lin_comp_market.Constraints.power_balance = TSOPowerBalance==0;

lin_comp_market.Constraints.upper_line_limit = Yline*theta<=FMAX*ones(1,T);
lin_comp_market.Constraints.lower_line_limit = -Yline*theta<=FMAX*ones(1,T);




%%%%% EVs %%%%%%%%%%%%%%%%%%%%
lin_a2 = optimconstr(max(nev)*nda,T);
lin_a3 = optimconstr(max(nev)*nda,T);
lin_SL_bin_con = optimconstr(max(nsl),T);
lin_a10 = optimconstr(max(nsl),T);

for ii=1:max([nev,ntcl,nsl])*nda
    if ii<=max(nev)*nda
        if EV_Arrivals_vec(ii)>0
            lin_a2(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii)) = ch(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii))<=(lin_u_ev(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii)).*repmat(EV_power_max_vec(ii),1,EV_Departures_vec(ii)-EV_Arrivals_vec(ii)+1));
            lin_a3(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii))=dis(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii))<=(1-lin_u_ev(ii,EV_Arrivals_vec(ii):EV_Departures_vec(ii))).*repmat(EV_power_max_vec(ii),1,EV_Departures_vec(ii)-EV_Arrivals_vec(ii)+1);
        end
    end
    
    if ii<=max(nsl)*nda
        if SL_start_vec(ii)>0
            lin_SL_bin_con(ii,[1:SL_start_vec(ii)-1,SL_end_vec(ii):end]) = lin_w(ii,[1:SL_start_vec(ii)-1,SL_end_vec(ii):end])==0;
            for tt=1:T
                if tt>=SL_start_vec(ii)&&tt<=SL_end_vec(ii)
                    if tt-SL_cycle_vec(ii)<0 % <= or <
                        lin_a10(ii,tt) = p_sl(ii,tt) == lin_w(ii,1:tt)*SL_profile_vec(ii,1:tt)';
                    else
                        lin_a10(ii,tt) = p_sl(ii,tt) == lin_w(ii,tt-[0:SL_cycle_vec(ii)-1])*SL_profile_vec(ii,1:SL_cycle_vec(ii))';
                    end
                else
                    lin_a10(ii,tt) = p_sl(ii,tt) == 0;
                end
            end
        else
            lin_a10(ii,:) = p_sl(ii,:) == 0;
        end
    end
    
end
lin_comp_market.Constraints.charge_power_limit = lin_a2;
lin_comp_market.Constraints.charge_power_limit_zero = ch_zero;
lin_comp_market.Constraints.discharge_power_limit = lin_a3;
lin_comp_market.Constraints.discharge_power_limit_zero = dis_zero;
lin_comp_market.Constraints.soet1 = a4t1;
lin_comp_market.Constraints.soet2 = a4t2;
lin_comp_market.Constraints.soe_last_timeslot = a6;
lin_comp_market.Constraints.tcl1 = a8;
lin_comp_market.Constraints.tcl2 = a9l;
if temp_upper_bound
    lin_comp_market.Constraints.tcl4 = a9r;
end
lin_comp_market.Constraints.tcl3 = initial_temp;
lin_comp_market.Constraints.sl1 = lin_SL_bin_con;
lin_comp_market.Constraints.sl2 = lin_a10;
lin_comp_market.Constraints.sl3 = sum(lin_w,2)==1;

lin_comp_market.Constraints.DA_portfolio_balance = da_buy-da_sell == InfLoad-p_res+sum_ch-sum_dis+sum_ptcl+sum_psl;

lin_comp_market.Constraints.offer_bigM1 = da_sell<=10000*lin_u_bigM;
lin_comp_market.Constraints.offer_bigM2 = da_buy<=10000*(1-lin_u_bigM);

lin_comp_market.Constraints.fix_u_ev = lin_u_ev == x_opt.u_ev;
lin_comp_market.Constraints.fix_w = lin_w == x_opt.w;
lin_comp_market.Constraints.fix_u_bigM = lin_u_bigM == x_opt.u_bigM;
% Objective
lin_comp_market.Objective = sum(sum(GenBids.*g))+sum(sum(da_price_offers.*da_sell))-sum(sum(da_price_bids.*da_buy));

% Solver
%[lin_x_opt,lin_Cost,lin_output,lin_exitflag,duals]=solve(lin_comp_market);
%results = gurobi(lin_comp_market);

Competitive_LMPs = duals.Constraints.power_balance;

DA_Competitive_Profits = sum((x_opt.da_sell*MVA-x_opt.da_buy*MVA).*(DALoc'*Competitive_LMPs),2);


%% Plot
plot(sum(InfLoad,1)*MVA-sum(x_opt.p_res,1)*MVA)
hold on
plot(sum(x_opt.g,1)*MVA)