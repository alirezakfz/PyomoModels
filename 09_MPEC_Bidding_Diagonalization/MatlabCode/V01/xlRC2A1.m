function CELL = xlRC2A1(ROW1,COL1,ROW2,COL2)
%% Returns the column characters of Excel given a certain column number
% Input COL : number of column
% Output CHAR : Character combination in Excel
    if COL1 <= 26 && COL2 <= 26                         % [A..Z]
        CHAR1 = char(mod(COL1-1,26)+1+64);
        CHAR2 = char(mod(COL2-1,26)+1+64);
        CELL = [CHAR1 num2str(ROW1) ':' CHAR2 num2str(ROW2)];
    elseif COL1 <= 26 && COL2 <= 702                   % [AA..ZZ]
        COL2 = COL2-26;    
        CHAR1 = char(mod(COL1-1,26)+1+64);
        CHAR21 = char(floor((COL2-1)/26)+1+64);
        CHAR20 = char(mod(COL2-1,26)+1+64);
        CHAR2 = [CHAR21 CHAR20];
        CELL = [CHAR1 num2str(ROW1) ':' CHAR2 num2str(ROW2)];
    elseif COL1 <= 26 && COL2 <= 16384                 % [AAA..XFD]
        COL2 = COL2-702; 
        CHAR1 = char(mod(COL1-1,26)+1+64);
        CHAR22 = char(floor((COL2-1)/676)+1+64);
        COL2=COL2-(floor((COL2-1)/676))*676;
        CHAR21 = char(floor((COL2-1)/26)+1+64);
        CHAR20 = char(mod(COL2-1,26)+1+64);
        CHAR2 = [CHAR22 CHAR21 CHAR20];
        CELL = [CHAR1 num2str(ROW1) ':' CHAR2 num2str(ROW2)];
    elseif COL1<=702 && COL2<=26
        COL1 = COL1-26;    
        CHAR2 = char(mod(COL2-1,26)+1+64);
        CHAR11 = char(floor((COL1-1)/26)+1+64);
        CHAR10 = char(mod(COL1-1,26)+1+64);
        CHAR1 = [CHAR11 CHAR10];
        CELL = [CHAR1 num2str(ROW1) ':' CHAR2 num2str(ROW2)];     
    elseif COL1<=702 && COL2<=702
        COL1 = COL1-26;
        COL2 = COL2-26;
        CHAR11 = char(floor((COL1-1)/26)+1+64);
        CHAR21 = char(floor((COL2-1)/26)+1+64);
        CHAR10 = char(mod(COL1-1,26)+1+64);
        CHAR20 = char(mod(COL2-1,26)+1+64);
        CHAR1 = [CHAR11 CHAR10];
        CHAR2 = [CHAR21 CHAR20];
        CELL = [CHAR1 num2str(ROW1) ':' CHAR2 num2str(ROW2)];
    elseif COL1<=702 && COL2<=16384
        COL1 = COL1-26;
        COL2 = COL2-702;
        CHAR11 = char(floor((COL1-1)/26)+1+64);
        CHAR10 = char(mod(COL1-1,26)+1+64);   
        CHAR22 = char(floor((COL2-1)/676)+1+64);
        CHAR21 = char(floor((COL2-1)/26)+1+64);
        CHAR20 = char(mod(COL2-1,26)+1+64);
        CHAR1 = [CHAR11 CHAR10];
        CHAR2 = [CHAR22 CHAR21 CHAR20];
        CELL = [CHAR1 num2str(ROW1) ':' CHAR2 num2str(ROW2)];
    elseif COL1<=16384 && COL2<=26
        COL1 = COL1 - 702;
        CHAR2 = char(mod(COL2-1,26)+1+64);
        CHAR12 = char(floor((COL1-1)/676)+1+64);
        CHAR11 = char(floor((COL1-1)/26)+1+64);
        CHAR10 = char(mod(COL1-1,26)+1+64);
        CHAR1 = [CHAR12 CHAR11 CHAR10];
        CELL = [CHAR1 num2str(ROW1) ':' CHAR2 num2str(ROW2)];
    elseif COL1<=16384 && COL2<=702
        COL1 = COL1 - 702;
        COL2 = COL2 - 26;
        CHAR12 = char(floor((COL1-1)/676)+1+64);
        CHAR11 = char(floor((COL1-1)/26)+1+64);
        CHAR10 = char(mod(COL1-1,26)+1+64);
        CHAR21 = char(floor((COL2-1)/26)+1+64);
        CHAR20 = char(mod(COL2-1,26)+1+64);
        CHAR1 = [CHAR12 CHAR11 CHAR10];
        CHAR2 = [CHAR21 CHAR20];
        CELL = [CHAR1 num2str(ROW1) ':' CHAR2 num2str(ROW2)];
    elseif COL1<=16384 && COL2<=16384
        COL1 = COL1 - 702;
        COL2 = COL2 - 702;
        CHAR12 = char(floor((COL1-1)/676)+1+64);
        CHAR11 = char(floor((COL1-1)/26)+1+64);
        CHAR10 = char(mod(COL1-1,26)+1+64);
        CHAR22 = char(floor((COL2-1)/676)+1+64);
        CHAR21 = char(floor((COL2-1)/26)+1+64);
        CHAR20 = char(mod(COL2-1,26)+1+64);
        CHAR1 = [CHAR12 CHAR11 CHAR10];
        CHAR2 = [CHAR22 CHAR21 CHAR20];
        CELL = [CHAR1 num2str(ROW1) ':' CHAR2 num2str(ROW2)];
    else
        disp('Column does not exist in Excel!');
    end
end