import { Platform } from 'react-native';

// Widget ile paylaşılan App Group. app.json ve targets/widget/SharedSettings.swift ile aynı olmalı.
export const APP_GROUP = 'group.com.ramazan29arslan.pati';

type Storage = {
  set(key: string, value?: string | number): void;
  get(key: string): string | null;
};

let storage: Storage | null = null;
let reload: (() => void) | null = null;

if (Platform.OS === 'ios') {
  try {
    // Native modül yalnızca iOS derlemesinde (EAS / prebuild) bulunur, Expo Go'da yoktur.
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

export function saveBattery(level: number | null, charging: boolean) {
  if (level !== null && level >= 0) storage?.set('batteryPercent', Math.round(level * 100));
  storage?.set('batteryCharging', charging ? 1 : 0);
}

export function reloadWidgets() {
  reload?.();
}
