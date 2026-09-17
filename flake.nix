{
  description = "Development and test environment for the KiCad Move Aligned To plugin";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python312;
        pythonEnv = python.withPackages (ps: with ps; [
          jsonschema
          kicad-python
          protobuf
          pynng
          pytest
          ruff
          tkinter
          typing-extensions
          zstandard
        ]);
        plugin = pkgs.stdenvNoCC.mkDerivation {
          pname = "kicad-move-aligned-to";
          version = "0.1.0";
          src = self;
          installPhase = ''
            runHook preInstall
            target="$out/share/kicad/plugins/com.github.unguentum.kicad-move-aligned-to"
            mkdir -p "$target"
            cp plugin.json requirements.txt main.py "$target/"
            cp -r move_aligned_to "$target/"
            runHook postInstall
          '';
        };
        installScript = pkgs.writeShellApplication {
          name = "install-plugin";
          runtimeInputs = [ pkgs.coreutils ];
          text = ''
            version="''${KICAD_VERSION:-10.0}"
            destination="''${XDG_DATA_HOME:-$HOME/.local/share}/KiCad/$version/plugins/com.github.unguentum.kicad-move-aligned-to"
            mkdir -p "$(dirname "$destination")"
            rm -rf "$destination"
            cp -r ${plugin}/share/kicad/plugins/com.github.unguentum.kicad-move-aligned-to "$destination"
            chmod -R u+w "$destination"
            echo "Installed Move Aligned To at $destination"
          '';
        };
        testScript = pkgs.writeShellApplication {
          name = "test-plugin";
          runtimeInputs = [ pythonEnv ];
          text = ''
            export PYTHONPATH="$PWD''${PYTHONPATH:+:$PYTHONPATH}"
            pytest -q
            ruff check .
            kicad-python-packager validate .
          '';
        };
      in {
        packages.default = plugin;

        apps.install = {
          type = "app";
          program = "${installScript}/bin/install-plugin";
        };
        apps.test = {
          type = "app";
          program = "${testScript}/bin/test-plugin";
        };

        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.git
            pkgs.kicad
            pkgs.scrot
            pkgs.xdotool
            pkgs.xvfb
          ];
          shellHook = ''
            export PYTHONPATH="$PWD:$PYTHONPATH"
            echo "Move Aligned To: pytest | ruff check . | nix run .#install"
          '';
        };
      });
}
