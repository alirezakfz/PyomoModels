clear,clc,close all
% 6-Bus Network from EPSR paper
% Line No. | From Bus | To Bus | Susceptance (p.u.) | Capacity (MW)
%    1     |     1    |    2   |       5.8824       |     150
%    2     |     1    |    4   |       3.8760       |     150
%    3     |     2    |    3   |       27.027       |     150
%    4     |     2    |    4   |       5.0761       |      33
%    5     |     3    |    6   |       55.5556      |     150
%    6     |     4    |    5   |       27.0270      |     150
%    7     |     5    |    6   |       7.1429       |     150

% Generation Unit | Bus No.  
%         1       |    1     
%         2       |    2    
%         3       |    6    
%         4       |    6    

%  Competing DA | Bus No. 
%       1       |    3    
%       2       |    3 
%       3       |    3 
%       4       |    4    
%       5       |    4 
%       6       |    4 
%       7       |    5 
%       8       |    5 
%       9       |    5 

T = 5; % Number of Timeslots

MVA = 30; % Power Base

nl = 7; % Number of network lines
nb = 6;  % Number of network buses

FromBus = [1,1,2,2,3,4,5]; % Vector with network lines' "sending buses"
ToBus = [2,4,3,4,6,5,6];   % Vector with network lines' "receiving buses"

LinesSusc = [5.8824, 3.8760, 27.0270, 5.0761, 55.5556, 27.0270, 7.1429]; % Vector with per unit susceptance of the network lines

ng = 4;   % Number of Generators
ncda = 9; % Number of competing DAs

GenBus = [1,2,6,6]; % Vector with Generation Buses
CDABus = [3,3,3,4,4,4,5,5,5];     % Vector with competing DAs Buses
DABus = 3;          % DA Bus

FMAX = [150,150,150,33,150,150,150]./MVA; % Vector with Capacities of Network Lines in pu

% Matrix (nb x ng) indicating the network location of generators
GenLoc = zeros(nb,ng);
for gg=1:ng
    GenLoc(GenBus(gg),gg) = 1;
end

% Matrix (nb x ncda) indicating the network location of competing DAs
CDALoc = zeros(nb,ncda);
for dd=1:ncda
    CDALoc(CDABus(dd),dd) = 1;
end

% Vector (nb x 1) indicating the network location of the DA
DALoc = zeros(nb,1);
DALoc(DABus) = 3;

% Optimization variables
g = optimvar('g',ng,T);
do = optimvar('do',ncda,T);
db = optimvar('db',ncda,T);
EdaUp = optimvar('EdaUp',1,T);
EdaDn = optimvar('EdaDn',1,T);
theta = optimvar('theta',nb,T);
flmin = optimvar('flmin',nl,T);
flmax = optimvar('flmax',nl,T);
ulmin = optimvar('ulmin',nl,T);
ulmax = optimvar('ulmax',nl,T);
lamda = optimvar('lamda',nb,T);

% Big-M constant
M = 100000;

%% 1) Bus Admittance Matrix Construction
B = zeros(nb); % Initialize Bus Admittance Matrix as an all-zero nxn matrix
for kk=1:nl
    % Off Diagonal elements of Bus Admittance Matrix
    B(FromBus(kk),ToBus(kk)) = -LinesSusc(kk);
    B(ToBus(kk),FromBus(kk)) = B(FromBus(kk),ToBus(kk));
end

% Diagonal Elements of B Matrix
for ii=1:nb
    B(ii,ii) = -sum(B(ii,:));
end


%% 2) Power Balance Constraint
TSOPowerBalance = optimexpr(nb,T);
for tt=1:T
    TSOPowerBalance(:,tt) = -GenLoc*g(:,tt)-CDALoc*(do(:,tt)-db(:,tt))-DALoc*(EdaUp(:,tt)-EdaDn(:,tt))+B*theta(:,tt);
end

%% 3) Line Flow Bounds (b.8)
% LineFlows Matrix indicates the starting and ending nodes of each line
LineFlows = zeros(nl,nb);
for kk=1:nl
    LineFlows(kk,FromBus(kk)) = 1;
    LineFlows(kk,ToBus(kk)) = -1;
end

% Yline Matrix
Yline = (LineFlows'.*LinesSusc)';

LineFlowsUpperBound = optimconstr(nl,T); % Upper Bounds on Line Flows
LineFlowsLowerBound = optimconstr(nl,T); % Lower Bounds on Line Flows
for tt=1:T
    LineFlowsUpperBound(:,tt) = Yline*theta(:,tt)<=FMAX';
    LineFlowsLowerBound(:,tt) = -Yline*theta(:,tt)<=FMAX';
end

%% 4) Constraint (c.6)
c6 = optimconstr(nb,T);
for tt=1:T
    c6(:,tt) = B'*lamda(:,tt)-Yline'*flmin(:,tt)+Yline'*flmax(:,tt) == 0;
end

%% 5) Constraints (d.21)-(d.23)
d21 = optimconstr(nl,T);
d23 = optimconstr(nl,T);
for tt=1:T
    d21(:,tt) = Yline*theta(:,tt)+FMAX'<=M*ulmin(:,tt);
    d23(:,tt) = -Yline*theta(:,tt)+FMAX'<=M*ulmax(:,tt);
end