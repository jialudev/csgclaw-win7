package main

import (
	"context"
	"errors"
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"

	"csgclaw/cli/csgclawcli"
	"csgclaw/internal/netcompat"
)

func main() {
	log.SetFlags(0)
	if err := run(os.Args[1:]); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return
		}
		log.Fatal(err)
	}
}

func run(args []string) error {
	netcompat.ConfigureDefaultHTTP()
	app := csgclawcli.New()
	return executeWithSignalContext(args, app.Execute)
}

func executeWithSignalContext(args []string, execFn func(context.Context, []string) error) error {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	return execFn(ctx, args)
}
