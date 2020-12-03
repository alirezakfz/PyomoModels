#!/bin/bash
# Must be run from pyomo/examples/pysp/networkflow
SourceDir="/home/woodruff/software/pyomo/src/pyomo.pysp/pyomo/pysp"

if [ "$1" == "" ]; then
   solver='gurobi'
else
   solver=$1
fi

echo
echo "run3.sh SourceDir is $SourceDir" 
python $SourceDir/lagrangeParam.py -m CCmodels -i CCdata/1ef3CC --solver=$solver --csvPrefix = "3" >> run3.out

