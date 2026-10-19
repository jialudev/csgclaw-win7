package codexcli

import (
	"reflect"
	"testing"
)

func TestWin7AppServerDisablesUnsupportedHostsAndKeepsOverrides(t *testing.T) {
	overrides := []string{"-c", `model="test-model"`}
	got := appServerArgs(overrides, true)
	want := []string{"app-server", "--disable", "plugins", "--disable", "code_mode", "--disable", "code_mode_host", "-c", `model="test-model"`, "--listen", "stdio://"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("Win7 app-server args = %q, want %q", got, want)
	}
	modern := appServerArgs(overrides, false)
	wantModern := []string{"app-server", "--disable", "plugins", "-c", `model="test-model"`, "--listen", "stdio://"}
	if !reflect.DeepEqual(modern, wantModern) {
		t.Fatalf("modern app-server args = %q, want %q", modern, wantModern)
	}
}
