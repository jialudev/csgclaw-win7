//go:build !windows

package netcompat

import "crypto/tls"

func TLSConfig() *tls.Config { return nil }
