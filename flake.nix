{
  description = "Set of command-line tools which need python";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python312;

        app = python.pkgs.buildPythonApplication {
          pname = "tools";
          version = "2025.07.05";
          src = builtins.path {
            path = ./.;
            name = "tools-src";
          };
          pyproject = true;
          nativeBuildInputs = [ pkgs.hatch ];
          propagatedBuildInputs = with python.pkgs; [ appdirs eyed3 ];
        };
      in {
        packages.default = app;
        apps.default = flake-utils.lib.mkApp { drv = app; name = "tools"; };
        devShells.default = pkgs.mkShell {
          buildInputs = [ pkgs.hatch python ];
        };
      });
}

