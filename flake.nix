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
          config.cudaSupport = true;
          config.cudnnSupport = true;
        };
      in
      {
        devShells.default = pkgs.mkShell{
          venvDir = ".venv";

          buildInputs = with pkgs; [
            python312
            python312Packages.venvShellHook
            python312Packages.torch
            # python312Packages.torchvision-bin
            python312Packages.torchaudio

            uv

            # MeloTTS
            mecab
            rustc
            cargo
            openssl
            openssl.dev

            # Whisper
            ffmpeg

            # Sound
            portaudio
          ];


          postVenvCreation = ''
            uv sync
            python -m unidic download
          '';

          shellHook = ''
            venvShellHook
            uv sync
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.portaudio}/lib
          '';

          # LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath buildInputs;
        };
      });
}
