{
  description = "Setup python with .venv";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          system = system;
          config.allowUnfree = true;
          overlays = [
            (final: prev: {
              python312 = prev.python312.override {
                packageOverrides = final: prevPy: {

                  triton-bin = prevPy.triton-bin.overridePythonAttrs (oldAttrs: {
                    postFixup = ''
                      chmod +x "$out/${prev.python312.sitePackages}/triton/backends/nvidia/bin/ptxas"
                      substituteInPlace $out/${prev.python312.sitePackages}/triton/backends/nvidia/driver.py \
                        --replace \
                          'return [libdevice_dir, *libcuda_dirs()]' \
                          'return [libdevice_dir, "${prev.addDriverRunpath.driverLink}/lib", "${prev.cudaPackages.cuda_cudart}/lib/stubs/"]'
                    '';
                  });
                };
              };
              python312Packages = final.python312.pkgs;
            })
          ];
        };
      in
      {
        devShells.default = pkgs.mkShell {
          venvDir = ".venv";

          buildInputs = with pkgs; [
            python312
            python312Packages.venvShellHook
            python312Packages.torch-bin
            # python312Packages.torchvision-bin
            python312Packages.torchaudio-bin

            uv
            mecab
            rustc
            cargo

            openssl
            openssl.dev
          ];

          postVenvCreation = ''
            uv sync
            python -m unidic download
          '';

          shellHook = ''
            venvShellHook
            uv sync
          '';
        };
      });
}
