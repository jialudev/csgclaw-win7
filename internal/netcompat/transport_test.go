package netcompat

import (
	"crypto/tls"
	"crypto/x509"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestLegacyTrustPreservesVerification(t *testing.T) {
	server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()
	base := &http.Transport{TLSHandshakeTimeout: time.Second, TLSClientConfig: &tls.Config{MinVersion: tls.VersionTLS13}}
	trusted := transportWithRoots(base, rootPool([]*x509.Certificate{server.Certificate()}))
	defer trusted.CloseIdleConnections()
	response, err := (&http.Client{Transport: trusted}).Get(server.URL)
	if err != nil {
		t.Fatalf("trust locally installed root: %v", err)
	}
	response.Body.Close()
	if response.TLS == nil || len(response.TLS.VerifiedChains) == 0 {
		t.Fatal("HTTPS connection did not verify its certificate chain")
	}
	if base.TLSClientConfig.RootCAs != nil || trusted.TLSClientConfig.InsecureSkipVerify || trusted.TLSClientConfig.MinVersion != tls.VersionTLS13 {
		t.Fatal("legacy roots changed the original transport or weakened TLS settings")
	}
	untrusted := transportWithRoots(base, rootPool(nil))
	defer untrusted.CloseIdleConnections()
	if response, err := (&http.Client{Transport: untrusted}).Get(server.URL); err == nil {
		response.Body.Close()
		t.Fatal("untrusted certificate was accepted")
	}
	wrongHost := transportWithRoots(base, rootPool([]*x509.Certificate{server.Certificate()}))
	defer wrongHost.CloseIdleConnections()
	wrongHost.TLSClientConfig.ServerName = "wrong-host.invalid"
	if response, err := (&http.Client{Transport: wrongHost}).Get(server.URL); err == nil {
		response.Body.Close()
		t.Fatal("certificate with an incorrect hostname was accepted")
	}
}

func TestBundledTrustContainsRoots(t *testing.T) {
	if len(rootPool(nil).Subjects()) < 50 {
		t.Fatal("Mozilla trust bundle is missing or invalid")
	}
}
