{
  description = "Miyakowasure Ryokan Availability Checker";

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

        miyakowasure-check = pkgs.stdenv.mkDerivation {
          pname = "miyakowasure-check";
          version = "0.1.0";

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
            mkdir -p $out/lib/miyakowasure-check
            cp -r src/miyakowasure_check $out/lib/miyakowasure-check/

            mkdir -p $out/bin
            makeWrapper ${pythonEnv}/bin/python $out/bin/miyakowasure-check \
              --set PYTHONPATH "$out/lib/miyakowasure-check" \
              --set PLAYWRIGHT_BROWSERS_PATH "${pkgs.playwright-driver.browsers}" \
              --set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD "1" \
              --add-flags "-m miyakowasure_check.cli"
          '';

          meta = with pkgs.lib; {
            description = "CLI tool to monitor room availability at Natsuse Onsen Miyakowasure ryokan";
            license = licenses.mit;
            maintainers = [ ];
            platforms = platforms.unix;
          };
        };

      in
      {
        packages = {
          default = miyakowasure-check;
          miyakowasure-check = miyakowasure-check;
        };

        apps.default = {
          type = "app";
          program = "${miyakowasure-check}/bin/miyakowasure-check";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.uv
            pkgs.python312
          ];

          shellHook = ''
            echo "Miyakowasure dev shell"
            echo "Run: uv sync && source .venv/bin/activate"
          '';
        };
      }
    );
}
