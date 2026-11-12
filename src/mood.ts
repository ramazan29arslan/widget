// targets/widget/Mood.swift ile aynı kurallar. Birini değiştirirsen diğerini de güncelle.

export type Mood = 'awake' | 'sleepy' | 'sleeping' | 'tired' | 'playful';

export const MOODS: { id: Mood; title: string; letter: string }[] = [
  { id: 'awake', title: 'Uyanık', letter: 'a' },
  { id: 'sleepy', title: 'Uykulu', letter: 's' },
  { id: 'sleeping', title: 'Uyuyor', letter: 'z' },
  { id: 'tired', title: 'Yorgun', letter: 't' },
  { id: 'playful', title: 'Oyuncu', letter: 'p' },
];

export function moodInfo(mood: Mood) {
  return MOODS.find((m) => m.id === mood)!;
}

export type MoodInputs = {
  date: Date;
  /** 0...1, bilinmiyorsa null */
  batteryLevel: number | null;
  isCharging: boolean;
};

export function computeMood(input: MoodInputs, reactToBattery: boolean, override: Mood | null = null): Mood {
  if (override) return override;
  if (reactToBattery) {
    if (input.batteryLevel !== null && input.batteryLevel < 0.2 && !input.isCharging) return 'tired';
    if (input.isCharging) return 'sleeping';
  }
  const h = input.date.getHours();
  if (h < 6) return 'sleeping';
  if (h < 8) return 'sleepy';
  if (h >= 13 && h < 15) return 'sleepy';
  if (h >= 17 && h < 20) return 'playful';
  if (h >= 22) return 'sleepy';
  return 'awake';
}
