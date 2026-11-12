import { Platform } from 'react-native';

import type { Mood } from './mood';

// Widget ile paylaşılan App Group. app.config.js ve targets/widget/SharedSettings.swift ile aynı olmalı.
export const APP_GROUP = 'group.com.ramazan29arslan.pati';

type Storage = {
  set(key: string, value?: string | number): void;
  get(key: string): string | null;
};

let storage: Storage | null = null;
let reload: (() => void) | null = null;

if (Platform.OS === 'ios') {
  try {
    // Native modül yalnızca derlenmiş iOS uygulamasında bulunur, Expo Go'da yoktur.
    const { ExtensionStorage } = require('@bacons/apple-targets');
    storage = new ExtensionStorage(APP_GROUP);
    reload = () => ExtensionStorage.reloadWidget();
  } catch {
    storage = null;
  }
}

export const widgetBridgeAvailable = () => storage !== null;

export function getReactToBattery(): boolean {
  const v = storage?.get('reactToBattery');
  return v === null || v === undefined ? true : v !== '0';
}

/** Widget tarafında Int okunur (ExtensionStorage sayıları Int kaydeder). */
export function setReactToBattery(on: boolean) {
  storage?.set('reactToBattery', on ? 1 : 0);
  reloadWidgets();
}

/** Elle seçilen ruh hali; null = otomatik. */
export function getMoodOverride(): Mood | null {
  const v = storage?.get('moodOverride');
  return (v || null) as Mood | null;
}

export function setMoodOverride(mood: Mood | null) {
  // Değer verilmezse anahtar silinir.
  storage?.set('moodOverride', mood ?? undefined);
  reloadWidgets();
}

export function saveBattery(level: number | null, charging: boolean) {
  if (level !== null && level >= 0) storage?.set('batteryPercent', Math.round(level * 100));
  storage?.set('batteryCharging', charging ? 1 : 0);
}

export function reloadWidgets() {
  reload?.();
}
