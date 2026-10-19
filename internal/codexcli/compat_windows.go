//go:build windows

package codexcli

import "golang.org/x/sys/windows"

func legacyWindows() bool {
	version := windows.RtlGetVersion()
	return version.MajorVersion == 6 && version.MinorVersion == 1
}
