export type AnimationClip = {
  id: string;
  title: string;
  /** Fontun PostScript adı. Rakamlar 0-9 klibin 10 karesidir. */
  fontName: string;
};

export type PatiCharacter = {
  id: string;
  name: string;
  clips: AnimationClip[];
  /** Pozların bulunduğu font. Her poz bir harftir (bkz. Mood). */
  poseFontName: string;
  poses: string[];
};
