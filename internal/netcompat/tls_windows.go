//go:build windows

package netcompat

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"sync"
	"unsafe"

	"golang.org/x/sys/windows"
)

var legacyRoots struct {
	sync.Once
	pool *x509.CertPool
}

// TLSConfig keeps Win7 HTTPS verification local instead of invoking Crypt32's
// retired automatic root-update service during every TLS handshake.
func TLSConfig() *tls.Config {
	version := windows.RtlGetVersion()
	if version.MajorVersion != 6 || version.MinorVersion != 1 {
		return nil
	}
	legacyRoots.Do(func() { legacyRoots.pool = rootPool(windowsRootCertificates()) })
	return &tls.Config{RootCAs: legacyRoots.pool}
}

func windowsRootCertificates() []*x509.Certificate {
	name, err := windows.UTF16PtrFromString("ROOT")
	if err != nil {
		return nil
	}
	store, err := windows.CertOpenSystemStore(0, name)
	if err != nil {
		return nil
	}
	defer windows.CertCloseStore(store, 0)
	var certificates []*x509.Certificate
	var current *windows.CertContext
	for {
		// Enumeration frees the previous context, including on the final call.
		current, err = windows.CertEnumCertificatesInStore(store, current)
		if err != nil || current == nil {
			break
		}
		der := bytes.Clone(unsafe.Slice(current.EncodedCert, current.Length))
		if certificate, parseErr := x509.ParseCertificate(der); parseErr == nil {
			certificates = append(certificates, certificate)
		}
	}
	return certificates
}
