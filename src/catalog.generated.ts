// BU DOSYA OTOMATİK ÜRETİLİR. Düzenleme: Tools/fontgen/build_fonts.py
import type { PatiCharacter } from './types';

export const FONTS = {
  "Pati-cat-tail": require('../targets/widget/assets/Pati-cat-tail.ttf'),
  "Pati-cat-breathe": require('../targets/widget/assets/Pati-cat-breathe.ttf'),
  "Pati-cat-walk": require('../targets/widget/assets/Pati-cat-walk.ttf'),
  "Pati-cat-roll": require('../targets/widget/assets/Pati-cat-roll.ttf'),
  "Pati-cat-poses": require('../targets/widget/assets/Pati-cat-poses.ttf'),
};

export const CHARACTERS: PatiCharacter[] = [
  {
    id: "cat",
    name: "Kedi",
    clips: [
      { id: "tail", title: "Kuyruk sallama", fontName: "Pati-cat-tail" },
      { id: "breathe", title: "Uykuda nefes", fontName: "Pati-cat-breathe" },
      { id: "walk", title: "Yürüyüş", fontName: "Pati-cat-walk" },
      { id: "roll", title: "Yuvarlanma", fontName: "Pati-cat-roll" },
    ],
    poseFontName: "Pati-cat-poses",
    poses: ["a", "s", "z", "t", "p"],
  },
];
