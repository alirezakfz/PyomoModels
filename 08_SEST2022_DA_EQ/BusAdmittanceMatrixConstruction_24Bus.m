clear,clc,close all
% 6-Bus Network from EPSR paper
% Line No.  | From Bus | To Bus  | Susceptance (p.u.) | Capacity (MW)
%    1      |     1    |    2    |       68.49315068  |     150
%    2      |     1    |    3    |       4.438526409  |     150
%    3      |     1    |    5    |       11.02535832  |     150
%    4      |     2    |    4    |       7.374631268  |      33
%    5      |     2    |    6    |       4.87804878   |     150
%    6      |     3    |    9    |       7.867820614  |     150
%    7      |     3    |    24   |       11.9047619   |     150
%    8      |     4    |    9    |       9.009009009  |     150
%    9      |     5    |    10   |       10.63829787  |     150
%    10     |     6    |    10   |       15.57632399  |     150
%    11     |     7    |    8    |       15.33742331  |     150
%    12     |     8    |    9    |       5.675368899  |     150
%    13     |     8    |    10   |       5.675368899  |     150
%    14     |     9    |    11   |       7.1429       |     150
%    15     |     9    |    12   |       7.1429       |     150
%    16     |     10   |    11   |       7.1429       |     150
%    17     |     10   |    12   |       7.1429       |     150
%    18     |     11   |    13   |       7.1429       |     150
%    19     |     11   |    14   |       7.1429       |     150
%    20     |     12   |    13   |       7.1429       |     150
%    21     |     12   |    23   |       7.1429       |     150
%    22     |     13   |    23   |       7.1429       |     150
%    23     |     14   |    16   |       7.1429       |     150
%    24     |     15   |    16   |       7.1429       |     150
%    25     |     15   |    21   |       7.1429       |     150
%    26     |     15   |    24   |       7.1429       |     150
%    27     |     16   |    17   |       7.1429       |     150
%    28     |     16   |    19   |       7.1429       |     150
%    29     |     17   |    18   |       7.1429       |     150
%    30     |     17   |    22   |       7.1429       |     150
%    31     |     18   |    21   |       7.1429       |     150
%    32     |     19   |    20   |       7.1429       |     150
%    33     |     20   |    23   |       7.1429       |     150
%    34     |     21   |    22   |       7.1429       |     150

% Generation Unit | Bus No.  
%         1       |    1     
%         2       |    2    
%         3       |    6    
%         4       |    6    

%  Competing DA | Bus No. 
%       1       |    3    
%       2       |    4    

T = 5; % Number of Timeslots

MVA = 1; % Power Base

nl = 34; % Number of network lines
nb = 24;  % Number of network buses

FromBus = [1,1,1,2,2,3,3,4,5,6,7,8,8,9,9,10,10,11,11,12,12,13,14,15,15,15,16,16,17,17,18,19,20,21]; % Vector with network lines' "sending buses"
ToBus = [2,3,5,4,6,9,24,9,10,10,8,9,10,11,12,11,12,13,14,13,23,23,16,16,21,24,17,19,18,22,21,20,23,22];   % Vector with network lines' "receiving buses"

%LinesSusc = [68.49315068;4.438526409;11.02535832;7.374631268;4.87804878;7.867820614;11.9047619;9.009009009;10.63829787;15.57632399;15.33742331;5.675368899;5.675368899;11.9047619;11.9047619;11.9047619;11.9047619;20.49180328;23.4741784;20.49180328;10.15228426;11.31221719;16.83501684;58.13953488;40.16064257;18.90359168;38.02281369;42.73504274;69.93006993;9.35453695;75.75757576;49.26108374;89.28571429;14.45086705]; % Vector with per unit susceptance of the network lines
LinesSusc = [68.49315068,4.438526409,11.02535832,7.374631268,4.87804878,7.867820614,11.9047619,9.009009009,10.63829787,15.57632399,15.33742331,5.675368899,5.675368899,11.9047619,11.9047619,11.9047619,11.9047619,20.49180328,23.4741784,20.49180328,10.15228426,11.31221719,16.83501684,58.13953488,40.16064257,18.90359168,38.02281369,42.73504274,69.93006993,9.35453695,75.75757576,49.26108374,89.28571429,14.45086705];

ng = 12;   % Number of Generators
ncda = 16; % Number of competing DAs

GenBus = [1,2,7,13,15,15,16,18,21,22,23,23]; % Vector with Generation Buses
CDABus = [1,2,3,4,5,6,7,8,9,10,13,14,15,16,18,19,20];     % Vector with competing DAs Buses
DABus = 1;          % DA Bus

FMAX = [175,175,350,175,175,175,400,175,350,175,350,175,175,400,400,400,400,500,500,500,500,200,250,500,400,500,500,500,500,500,1000,1000,1000,500]./MVA; % Vector with Capacities of Network Lines in pu

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
DALoc(DABus) = 1;

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