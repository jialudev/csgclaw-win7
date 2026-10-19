// Package netcompat supplies HTTPS trust on legacy Windows without changing
// certificate verification, protocol negotiation, or modern-platform behavior.
package netcompat

import (
	"crypto/tls"
	"crypto/x509"
	_ "embed"
	"net/http"
)

//go:embed mozilla-roots.pem
var bundledRoots []byte

func rootPool(systemCertificates []*x509.Certificate) *x509.CertPool {
	// Do not use SystemCertPool here: its Windows systemPool flag sends Verify
	// back to Crypt32, whose missing-root retrieval blocks on unpatched Win7.
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(bundledRoots)
	for _, certificate := range systemCertificates {
		pool.AddCert(certificate)
	}
	return pool
}

// ConfigureDefaultHTTP enables the legacy trust store before creating clients.
// TLSConfig returns nil on platforms whose native verifier remains supported.
func ConfigureDefaultHTTP() {
	config := TLSConfig()
	if config == nil {
		return
	}
	if transport, ok := http.DefaultTransport.(*http.Transport); ok {
		http.DefaultTransport = transportWithRoots(transport, config.RootCAs)
	}
}

func transportWithRoots(base *http.Transport, roots *x509.CertPool) *http.Transport {
	transport := base.Clone()
	if transport.TLSClientConfig == nil {
		transport.TLSClientConfig = &tls.Config{}
	}
	transport.TLSClientConfig.RootCAs = roots
	return transport
}
