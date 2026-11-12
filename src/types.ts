export type AnimationClip = {
  id: string;
  title: string;
  /** Tek widget fontu (panoramada küçültülmüş tam sahne). Rakamlar 0-9 klibin 10 karesidir. */
  fontName: string;
  /** Panorama: iki widget'a yayılan klip. */
  wide: boolean;
  leftFont: string | null;
  rightFont: string | null;
};

export type PatiCharacter = {
  id: string;
  name: string;
  clips: AnimationClip[];
  /** Pozların bulunduğu font. Her poz bir harftir (bkz. Mood). */
  poseFontName: string;
  poses: string[];
  /** Ruh hali -> "Otomatik" modda oynatılacak klip */
  moodClips: Record<string, string>;
};
