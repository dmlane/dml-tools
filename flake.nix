{
  description = "Nix flake for dml-tools (Poetry CLI using Python 3.12)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-darwin"
      ];
      forAllSystems =
        f:
        nixpkgs.lib.genAttrs systems (
          system:
          f {
            pkgs = import nixpkgs { inherit system; };
            system = system;
          }
        );
    in
    {
      packages = forAllSystems (
        { pkgs, system }:
        let
          dmlToolsPkg = pkgs.python312Packages.buildPythonPackage {
            pname = "dml-tools";
            version = "2025.7.1034";
            format = "pyproject";

            src = ./.;

            nativeBuildInputs = [ pkgs.poetry ];
            propagatedBuildInputs = with pkgs.python312Packages; [
              eyed3
              appdirs
              poetry-core
            ];
            outputs = [ "out" ];
            pythonImportsCheck = [ "tools.car_podcasts" ];

            meta = {
              description = "Set of command-line tools (dml-tools)";
              homepage = "https://github.com/dmlane/dml-tools";
              license = pkgs.lib.licenses.mit;
            };
          };
        in
        {
          default = dmlToolsPkg;
          dml-tools = dmlToolsPkg;
        }
      );

      devShells = forAllSystems (
        { pkgs, ... }:
        {
          default = pkgs.mkShell {
            buildInputs = [
              pkgs.poetry
              pkgs.python312
            ];
          };
        }
      );
    };
}
