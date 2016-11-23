#!/bin/sh
# You can edit this on your local copy to run a single test or a selected set
# of tests. This can be useful when you are working in one area and want a
# fast turn around. You should however always have all the tests on
# when you check this in.

echo "==========================================================="
echo "Can specify run_test=<exp> on command line to run subset of"
echo "unit tests. See boost unit test documentation for details"
echo ""
echo "If log_test is defined, add verbose information as each"
echo "test is run."
echo ""
echo "If valgrind is defined, then we run the test with valgrind."
echo ""
echo "==========================================================="

if [ ${valgrind} ] ; then
    tool_command="valgrind --max-stackframe=5000000 --error-exitcode=1 --track-origins=yes --suppressions=$(dirname $0)/../config/valgrind.suppressions"
elif [ ${gdb} ]; then
    tool_command="gdb --args"
else
    tool_command=""
fi

source ../script/setup_ecostress.sh

if [ ${log_test} ] ; then
    ${tool_command} ./ecostress_test_all --log_level=test_suite --run_test=${run_test}
else
    ${tool_command} ./ecostress_test_all --show_progress --run_test=${run_test}
fi

# Valgrind version of test run. 
#valgrind --suppressions=${srcdir}/test_data/valgrind.suppressions ./lib/test_all --log_level=test_suite

