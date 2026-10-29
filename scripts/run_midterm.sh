#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# On macOS select the installed JDK 21 for Maven and the benchmark alike.
if [ -x /usr/libexec/java_home ]; then
  JAVA_HOME=$(/usr/libexec/java_home -v 21)
  export JAVA_HOME
  PATH="$JAVA_HOME/bin:$PATH"
  export PATH
fi
# No private keys are persisted in artifacts. Each execution gets its own folder.
run_dir="artifacts/run-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$run_dir"
python3 scripts/create_documents.py
python3 scripts/create_team_presentation.py
python3 scripts/verify_data.py > "$run_dir/data-check.log"
java -version > "$run_dir/environment.txt" 2>&1
mvn -version >> "$run_dir/environment.txt" 2>&1
openssl version >> "$run_dir/environment.txt"
python3 --version >> "$run_dir/environment.txt"
if command -v sysctl >/dev/null 2>&1; then
  sysctl -n machdep.cpu.brand_string hw.memsize >> "$run_dir/environment.txt" 2>/dev/null || true
fi
mvn clean test > "$run_dir/junit.log" 2>&1 || { cat "$run_dir/junit.log"; exit 1; }
cp target/surefire-reports/TEST-*.xml "$run_dir/"
java -cp target/classes vn.edu.atbm.mssv1150080127.experiment.MidtermBenchmark "$run_dir" > "$run_dir/benchmark.log" 2>&1
python3 scripts/summarize_results.py "$run_dir"
python3 scripts/package_evidence.py "$run_dir"
echo "Evidence: $run_dir"
