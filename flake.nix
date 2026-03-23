{
  description = "Sustainable GitHub Workflow Linter";

  inputs = {
    nixpkgs.url = "http://nixos.org/channels/nixos-25.11/nixexprs.tar.xz";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { nixpkgs, pyproject-nix, ... }:
  let
    systems = [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ];

    forEachSystem = nixpkgs.lib.genAttrs systems;

  in {
    packages = forEachSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;

        project = pyproject-nix.lib.project.loadPyproject {
          projectRoot = ./.;
        };

        attrs = project.renderers.buildPythonPackage {
          inherit python;
        };

        package = python.pkgs.buildPythonApplication attrs;

      in {
        default = package;
      }
    );

    devShells = forEachSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;

        project = pyproject-nix.lib.project.loadPyproject {
          projectRoot = ./.;
        };

        arg = project.renderers.withPackages { inherit python; };
        pythonEnv = python.withPackages arg;

      in {
        default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.python3Packages.mypy
            pkgs.python3Packages.pytest
          ];

          shellHook = ''
            if [ ! -d .venv ]; then
              python -m venv .venv
            fi
            source .venv/bin/activate

            pip install -e .[dev]
          '';
        };
      }
    );
  };
}