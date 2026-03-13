{
  description = "Sustainable GitHub Workflow Linter";

  inputs = {
    nixpkgs.url = "http://nixos.org/channels/nixos-25.11/nixexprs.tar.xz";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    { nixpkgs, pyproject-nix, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      python = pkgs.python3;

      project = pyproject-nix.lib.project.loadPyproject {
        projectRoot = ./.;
      };

      # attrs for buildPythonPackage
      attrs = project.renderers.buildPythonPackage {
        inherit python;
      };

      package = python.pkgs.buildPythonApplication attrs;
      # buildPythonApplication ensures scripts are exposed properly
    in
    {
      packages.${system}.default = package;

      devShells.${system}.default =
        let
          arg = project.renderers.withPackages { inherit python; };
          pythonEnv = python.withPackages arg;
        in
        pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.python3Packages.mypy
          ];
        };
    };
}
