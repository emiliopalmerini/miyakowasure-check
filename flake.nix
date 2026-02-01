{
  description = "Ryokan Availability Checker - Monitor room availability at Japanese ryokan";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python = pkgs.python312;

        pythonDeps = ps: with ps; [
          playwright
          httpx
          typer
          rich
        ];

        pythonEnv = python.withPackages pythonDeps;

        ryokan-check = pkgs.stdenv.mkDerivation {
          pname = "ryokan-check";
          version = "0.2.0";

          src = ./.;

          nativeBuildInputs = [
            pythonEnv
            pkgs.makeWrapper
          ];

          buildInputs = [
            pythonEnv
            pkgs.playwright-driver.browsers
          ];

          installPhase = ''
            mkdir -p $out/lib/ryokan-check
            cp -r src/ryokan_check $out/lib/ryokan-check/

            mkdir -p $out/bin
            makeWrapper ${pythonEnv}/bin/python $out/bin/ryokan-check \
              --set PYTHONPATH "$out/lib/ryokan-check" \
              --set PLAYWRIGHT_BROWSERS_PATH "${pkgs.playwright-driver.browsers}" \
              --set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD "1" \
              --add-flags "-m ryokan_check.cli"
          '';

          meta = with pkgs.lib; {
            description = "CLI tool to monitor room availability at Japanese ryokan (Miyakowasure, Miyamaso Takamiya)";
            license = licenses.mit;
            maintainers = [ ];
            platforms = platforms.unix;
          };
        };

      in
      {
        packages = {
          default = ryokan-check;
          ryokan-check = ryokan-check;
        };

        apps.default = {
          type = "app";
          program = "${ryokan-check}/bin/ryokan-check";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.uv
            pkgs.python312
          ];

          shellHook = ''
            echo "Ryokan-check dev shell"
            echo "Run: uv sync && source .venv/bin/activate"
          '';
        };
      }
    );
}
