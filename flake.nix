{
  description = "Patched KiCad with the Move Aligned To plugin";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      overlay = final: prev:
        let
          plugin = final.kicad-unstable.callPackage
            ({ stdenvNoCC, zip, addonPath, python3 }:
              stdenvNoCC.mkDerivation {
                pname = "kicad-addon-move-aligned-to";
                version = "0.1.0";
                src = self;
                nativeBuildInputs = [ zip ];
                dontConfigure = true;
                dontBuild = true;
                installPhase = ''
                  runHook preInstall
                  identifier=com.github.unguentum.kicad-move-aligned-to
                  mkdir -p package/plugins/$identifier $out
                  cp plugin.json requirements.txt main.py package/plugins/$identifier/
                  cp -r move_aligned_to package/plugins/$identifier/
                  printf '{"identifier":"%s"}\n' "$identifier" > package/metadata.json
                  (cd package && zip -qr "$out/${addonPath}" .)
                  runHook postInstall
                '';
              }) { };

          patchedSource = final.applyPatches {
            name = "kicad-axis-constrained-move-source";
            src = prev.kicad-unstable.base.src;
            patches = [ ./patches/0001-Expose-axis-constrained-interactive-move-over-IPC.patch ];
          };

          kicadWithPlugin = prev.kicad-unstable.override {
            addons = [ plugin ];
            srcs = {
              kicad = patchedSource;
              kicadVersion = "10.99-axis-constrained-move";
            };
          };
        in {
          kicad-axis-constrained-move-addon = plugin;
          kicad-axis-constrained-move = kicadWithPlugin;
        };
    in
    {
      overlays.default = overlay;
    }
    // flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlay ];
        };
        python = pkgs.python312;
        pythonEnv = python.withPackages (ps: with ps; [
          jsonschema
          kicad-python
          protobuf
          pynng
          pytest
          ruff
          typing-extensions
          wxpython
          zstandard
        ]);
        testPythonEnv = python.withPackages (ps: with ps; [
          jsonschema
          kicad-python
          protobuf
          pynng
          pytest
          ruff
          typing-extensions
          zstandard
        ]);
        patchedKiCad = pkgs.kicad-axis-constrained-move;
        testScript = pkgs.writeShellApplication {
          name = "test-plugin";
          runtimeInputs = [ testPythonEnv ];
          text = ''
            export PYTHONPATH="$PWD''${PYTHONPATH:+:$PYTHONPATH}"
            pytest -q
            ruff check .
            kicad-python-packager validate .
          '';
        };
      in {
        packages = {
          default = patchedKiCad;
          patched-kicad = patchedKiCad;
          plugin = pkgs.kicad-axis-constrained-move-addon;
        };

        apps.default = {
          type = "app";
          program = "${patchedKiCad}/bin/kicad";
        };
        apps.test = {
          type = "app";
          program = "${testScript}/bin/test-plugin";
        };

        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.git
            patchedKiCad
            pkgs.scrot
            pkgs.xdotool
            pkgs.xvfb
          ];
          shellHook = ''
            export PYTHONPATH="$PWD:$PYTHONPATH"
            echo "Move Aligned To: pytest | ruff check . | nix run .#test"
          '';
        };
      });
}
