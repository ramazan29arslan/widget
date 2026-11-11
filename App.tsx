import * as Battery from 'expo-battery';
import { useFonts } from 'expo-font';
import { StatusBar } from 'expo-status-bar';
import { ReactNode, useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  AppState,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';

import { CHARACTERS, FONTS } from './src/catalog.generated';
import { Glyph } from './src/Glyph';
import { computeMood, Mood, MOODS, moodInfo } from './src/mood';
import type { PatiCharacter } from './src/types';
import {
  getReactToBattery,
  reloadWidgets,
  saveBattery,
  setReactToBattery,
  widgetBridgeAvailable,
} from './src/widgetBridge';

const C = {
  bg: '#1A0B10',
  card: '#2A1219',
  lock: '#341620',
  text: '#F6DEE4',
  dim: '#B89AA3',
  accent: '#E7899B',
};

export default function App() {
  const [fontsLoaded] = useFonts(FONTS);
  const [selected, setSelected] = useState<PatiCharacter | null>(null);

  if (!fontsLoaded) {
    return (
      <View style={[styles.screen, styles.center]}>
        <ActivityIndicator color={C.accent} />
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <StatusBar style="light" />
      {selected ? (
        <CharacterScreen character={selected} onBack={() => setSelected(null)} />
      ) : (
        <HomeScreen onSelect={setSelected} />
      )}
    </View>
  );
}

// MARK: - Ana ekran

function HomeScreen({ onSelect }: { onSelect: (c: PatiCharacter) => void }) {
  return (
    <ScrollView contentContainerStyle={styles.content}>
      <Text style={styles.title}>Pati</Text>
      <Text style={styles.subtitle}>Kilit ekranında yaşayan karakterler</Text>

      <Text style={styles.section}>Karakterler</Text>
      {CHARACTERS.map((c) => (
        <Pressable key={c.id} style={styles.row} onPress={() => onSelect(c)}>
          <Glyph fontName={c.clips[0].fontName} width={110} />
          <Text style={styles.rowTitle}>{c.name}</Text>
          <Text style={styles.chevron}>›</Text>
        </Pressable>
      ))}

      <Text style={styles.section}>Ruh hali</Text>
      <MoodSettings />

      <Text style={styles.section}>Widget nasıl eklenir?</Text>
      <View style={styles.card}>
        <Text style={styles.body}>
          Kilit ekranına basılı tut → Özelleştir → Kilit Ekranı → saatin altındaki alana dokun →
          Pati'yi seç. "Canlı Pati" saniyede bir kare oynar, "Ruh Hali Pati" saate ve şarja göre poz
          değiştirir.
        </Text>
      </View>
    </ScrollView>
  );
}

function MoodSettings() {
  const [react, setReact] = useState(getReactToBattery);
  const [battery, setBattery] = useState<{ level: number | null; charging: boolean }>({
    level: null,
    charging: false,
  });

  const refresh = useCallback(async () => {
    try {
      const [level, state] = await Promise.all([
        Battery.getBatteryLevelAsync(),
        Battery.getBatteryStateAsync(),
      ]);
      const charging = state === Battery.BatteryState.CHARGING || state === Battery.BatteryState.FULL;
      const value = { level: level >= 0 ? level : null, charging };
      setBattery(value);
      // Widget pil okuyamazsa diye son bilgiyi paylaşılan alana yaz.
      saveBattery(value.level, value.charging);
      reloadWidgets();
    } catch {
      // Simülatörde pil bilgisi olmayabilir.
    }
  }, []);

  useEffect(() => {
    refresh();
    const subs = [
      Battery.addBatteryLevelListener(refresh),
      Battery.addBatteryStateListener(refresh),
      AppState.addEventListener('change', (s) => s === 'active' && refresh()),
    ];
    return () => subs.forEach((s) => s.remove());
  }, [refresh]);

  const mood: Mood = computeMood(
    { date: new Date(), batteryLevel: battery.level, isCharging: battery.charging },
    react,
  );

  return (
    <View style={styles.card}>
      <View style={styles.settingRow}>
        <Text style={styles.body}>Şarja tepki ver</Text>
        <Switch
          value={react}
          onValueChange={(v) => {
            setReact(v);
            setReactToBattery(v);
          }}
          trackColor={{ true: C.accent }}
        />
      </View>
      <View style={styles.settingRow}>
        <Text style={styles.body}>Şu anki ruh hali</Text>
        <Text style={[styles.body, { color: C.accent }]}>{moodInfo(mood).title}</Text>
      </View>
      <View style={styles.settingRow}>
        <Text style={styles.body}>Pil</Text>
        <Text style={styles.dim}>
          {battery.level === null ? '—' : `%${Math.round(battery.level * 100)}`}
          {battery.charging ? ' · şarjda' : ''}
        </Text>
      </View>
      {!widgetBridgeAvailable() && (
        <Text style={[styles.dim, { marginTop: 8 }]}>
          Widget bağlantısı bu ortamda yok (Expo Go veya web). EAS ile derlenen uygulamada çalışır.
        </Text>
      )}
    </View>
  );
}

// MARK: - Karakter ekranı

function CharacterScreen({ character, onBack }: { character: PatiCharacter; onBack: () => void }) {
  return (
    <ScrollView contentContainerStyle={styles.content}>
      <Pressable onPress={onBack} hitSlop={12}>
        <Text style={styles.back}>‹ Geri</Text>
      </Pressable>
      <Text style={styles.title}>{character.name}</Text>

      <Text style={styles.section}>Animasyonlar · saniyede 1 kare</Text>
      {character.clips.map((clip) => (
        <View key={clip.id} style={styles.clipRow}>
          <LockPreview>
            <Glyph fontName={clip.fontName} width={150} />
          </LockPreview>
          <Text style={styles.body}>{clip.title}</Text>
        </View>
      ))}

      <Text style={styles.section}>Ruh hali pozları</Text>
      <View style={styles.grid}>
        {MOODS.filter((m) => character.poses.includes(m.letter)).map((m) => (
          <View key={m.id} style={styles.gridItem}>
            <LockPreview>
              <Glyph fontName={character.poseFontName} letter={m.letter} width={140} />
            </LockPreview>
            <Text style={[styles.dim, { marginTop: 6 }]}>{m.title}</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

/** Kilit ekranındaki dikdörtgen widget boyutunda koyu kutu. */
function LockPreview({ children }: { children: ReactNode }) {
  return <View style={styles.lock}>{children}</View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  center: { alignItems: 'center', justifyContent: 'center' },
  content: { padding: 20, paddingTop: 64, paddingBottom: 48 },
  title: { color: C.text, fontSize: 34, fontWeight: '700' },
  subtitle: { color: C.dim, fontSize: 15, marginTop: 4 },
  section: {
    color: C.dim,
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginTop: 28,
    marginBottom: 10,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: C.card,
    borderRadius: 16,
    padding: 12,
    gap: 16,
    marginBottom: 10,
  },
  rowTitle: { color: C.text, fontSize: 18, fontWeight: '600', flex: 1 },
  chevron: { color: C.dim, fontSize: 28 },
  card: { backgroundColor: C.card, borderRadius: 16, padding: 16 },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  body: { color: C.text, fontSize: 16, lineHeight: 22 },
  dim: { color: C.dim, fontSize: 14 },
  back: { color: C.accent, fontSize: 17, marginBottom: 12 },
  clipRow: { flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: 12 },
  lock: {
    width: 170,
    height: 84,
    borderRadius: 16,
    backgroundColor: C.lock,
    alignItems: 'center',
    justifyContent: 'center',
  },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 14 },
  gridItem: { alignItems: 'center' },
});
