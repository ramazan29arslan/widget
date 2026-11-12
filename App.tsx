import * as Battery from 'expo-battery';
import { useFonts } from 'expo-font';
import { StatusBar } from 'expo-status-bar';
import { ReactNode, useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  AppState,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';

import { CHARACTERS, FONTS } from './src/catalog.generated';
import { Glyph } from './src/Glyph';
import { computeMood, Mood, MOODS, moodInfo } from './src/mood';
import type { AnimationClip, PatiCharacter } from './src/types';
import {
  getMoodOverride,
  getReactToBattery,
  reloadWidgets,
  saveBattery,
  setMoodOverride,
  setReactToBattery,
} from './src/widgetBridge';

const C = {
  bg: '#120709',
  card: '#22100F',
  cardHi: '#3A1A1E',
  line: '#3E2226',
  text: '#F6E7EA',
  dim: '#A98C93',
  accent: '#EE8FA2',
  lockTop: '#5A2630',
  lockBottom: '#1E0B10',
};

export default function App() {
  const [fontsLoaded] = useFonts(FONTS);
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
      <Home />
    </View>
  );
}

// MARK: - Ana ekran

function Home() {
  const { width } = useWindowDimensions();
  const [character, setCharacter] = useState<PatiCharacter>(CHARACTERS[0]);
  const [clipId, setClipId] = useState<string | null>(null); // null = ruh haline göre
  const [react, setReact] = useState(getReactToBattery);
  const [override, setOverride] = useState<Mood | null>(getMoodOverride);
  const battery = useBattery();
  const now = useClock();

  const mood = computeMood(
    { date: now, batteryLevel: battery.level, isCharging: battery.charging },
    react,
    override,
  );
  const clip: AnimationClip = useMemo(() => {
    const id = clipId ?? character.moodClips[mood];
    return character.clips.find((c) => c.id === id) ?? character.clips[0];
  }, [character, clipId, mood]);

  const chooseMood = (m: Mood | null) => {
    setOverride(m);
    setMoodOverride(m);
    setClipId(null);
  };

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <Text style={styles.title}>Pati</Text>
      <Text style={styles.subtitle}>Kilit ekranında yaşayan karakterler</Text>

      <LockScreen width={width - 32} now={now} character={character} clip={clip} mood={mood} />

      <Section title="Karakter">
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 10 }}>
          {CHARACTERS.map((c) => {
            const on = c.id === character.id;
            return (
              <Pressable
                key={c.id}
                onPress={() => {
                  setCharacter(c);
                  setClipId(null);
                }}
                style={[styles.charCard, on && styles.selected]}
              >
                <Glyph fontName={c.poseFontName} letter="a" width={120} />
                <Text style={[styles.chipText, on && { color: C.text }]}>{c.name}</Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </Section>

      <Section title="Animasyon" hint="Seçtiğin animasyon üstteki önizlemede oynar.">
        <View style={styles.grid}>
          <Chip label="Ruh haline göre" on={clipId === null} onPress={() => setClipId(null)} />
          {character.clips.map((c) => (
            <Chip
              key={c.id}
              label={c.title}
              badge={c.wide ? '4 kare' : undefined}
              on={clipId === c.id}
              onPress={() => setClipId(c.id)}
            />
          ))}
        </View>
      </Section>

      <Section
        title="Ruh hali"
        hint={
          override
            ? 'Elle seçildi. Widget\'lar bu ruh halinde kalır.'
            : 'Otomatik: saate ve şarja göre değişir.'
        }
      >
        <View style={styles.grid}>
          <Chip label="Otomatik" on={override === null} onPress={() => chooseMood(null)} />
          {MOODS.map((m) => (
            <Chip key={m.id} label={m.title} on={override === m.id} onPress={() => chooseMood(m.id)} />
          ))}
        </View>
        <View style={[styles.card, { marginTop: 12 }]}>
          <Row label="Şu anki ruh hali" value={moodInfo(mood).title} accent />
          <Row
            label="Pil"
            value={`${battery.level === null ? '—' : `%${Math.round(battery.level * 100)}`}${
              battery.charging ? ' · şarjda' : ''
            }`}
          />
          <View style={styles.row}>
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
        </View>
      </Section>

      <Section title="Kilit ekranına ekleme">
        <View style={styles.card}>
          <Step n={1} text="Kilit ekranına basılı tut → Özelleştir → Kilit Ekranı." />
          <Step n={2} text="Saatin altındaki alana dokun, Pati'yi bul." />
          <Step n={3} text="Tek widget için “Canlı Pati” ya da “Ruh Hali Pati” ekle." />
          <Step
            n={4}
            text="4 kareyi kaplamak için iki “Canlı Pati” ekle. Birine dokunup Yerleşim → Panorama – sol parça, diğerine sağ parça seç. Aynı karakteri ve animasyonu seç."
          />
        </View>
      </Section>
    </ScrollView>
  );
}

// MARK: - Kilit ekranı önizlemesi

function LockScreen({
  width,
  now,
  character,
  clip,
  mood,
}: {
  width: number;
  now: Date;
  character: PatiCharacter;
  clip: AnimationClip;
  mood: Mood;
}) {
  const slotW = (width - 48 - 10) / 2;
  const date = now.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', weekday: 'short' });
  const time = now.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  return (
    <View style={[styles.lock, { width }]}>
      <View style={styles.lockGlow} />
      <Text style={styles.lockDate}>{date}</Text>
      <Text style={styles.lockTime}>{time}</Text>
      <View style={styles.lockRow}>
        {clip.wide ? (
          <>
            <Slot width={slotW} align="flex-end">
              <Glyph fontName={clip.leftFont!} width={slotW} align="flex-end" />
            </Slot>
            <Slot width={slotW} align="flex-start">
              <Glyph fontName={clip.rightFont!} width={slotW} align="flex-start" />
            </Slot>
          </>
        ) : (
          <>
            <Slot width={slotW}>
              <Glyph fontName={clip.fontName} width={slotW - 8} />
            </Slot>
            <Slot width={slotW}>
              <Glyph fontName={character.poseFontName} letter={moodInfo(mood).letter} width={slotW - 8} />
            </Slot>
          </>
        )}
      </View>
      <Text style={styles.lockCaption}>
        {clip.wide
          ? `${clip.title} · panorama (sol + sağ)`
          : `${clip.title}  ·  Ruh hali: ${moodInfo(mood).title}`}
      </Text>
    </View>
  );
}

function Slot({
  width,
  children,
  align = 'center',
}: {
  width: number;
  children: ReactNode;
  align?: 'center' | 'flex-start' | 'flex-end';
}) {
  return <View style={[styles.slot, { width, height: width / 2.1, alignItems: align }]}>{children}</View>;
}

// MARK: - Küçük parçalar

function Section({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <View style={{ marginTop: 28 }}>
      <Text style={styles.section}>{title}</Text>
      {children}
      {hint ? <Text style={[styles.dim, { marginTop: 8 }]}>{hint}</Text> : null}
    </View>
  );
}

function Chip({ label, on, onPress, badge }: { label: string; on: boolean; onPress: () => void; badge?: string }) {
  return (
    <Pressable onPress={onPress} style={[styles.chip, on && styles.selected]} hitSlop={4}>
      <Text style={[styles.chipText, on && { color: C.text }]}>{label}</Text>
      {badge ? <Text style={styles.badge}>{badge}</Text> : null}
    </Pressable>
  );
}

function Row({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <View style={styles.row}>
      <Text style={styles.body}>{label}</Text>
      <Text style={[styles.body, { color: accent ? C.accent : C.dim }]}>{value}</Text>
    </View>
  );
}

function Step({ n, text }: { n: number; text: string }) {
  return (
    <View style={{ flexDirection: 'row', gap: 10, paddingVertical: 6 }}>
      <Text style={styles.stepNum}>{n}</Text>
      <Text style={[styles.body, { flex: 1 }]}>{text}</Text>
    </View>
  );
}

// MARK: - Hook'lar

function useClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 15000);
    return () => clearInterval(t);
  }, []);
  return now;
}

function useBattery() {
  const [battery, setBattery] = useState<{ level: number | null; charging: boolean }>({
    level: null,
    charging: false,
  });
  const refresh = useCallback(async () => {
    try {
      const [level, state] = await Promise.all([Battery.getBatteryLevelAsync(), Battery.getBatteryStateAsync()]);
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
    const subs: { remove: () => void }[] = [
      AppState.addEventListener('change', (s) => s === 'active' && refresh()),
    ];
    try {
      subs.push(Battery.addBatteryLevelListener(refresh), Battery.addBatteryStateListener(refresh));
    } catch {
      // Pil dinleyicisi olmayan ortamlar (web önizleme)
    }
    return () => subs.forEach((s) => s.remove());
  }, [refresh]);
  return battery;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  center: { alignItems: 'center', justifyContent: 'center' },
  content: { padding: 16, paddingTop: 64, paddingBottom: 56 },
  title: { color: C.text, fontSize: 34, fontWeight: '800', letterSpacing: -0.5 },
  subtitle: { color: C.dim, fontSize: 15, marginTop: 2, marginBottom: 18 },
  section: {
    color: C.dim,
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  lock: {
    borderRadius: 28,
    paddingTop: 22,
    paddingBottom: 18,
    paddingHorizontal: 24,
    backgroundColor: C.lockBottom,
    overflow: 'hidden',
    alignItems: 'center',
  },
  lockGlow: {
    position: 'absolute',
    top: -260,
    left: -120,
    right: -120,
    height: 520,
    borderRadius: 520,
    backgroundColor: C.lockTop,
    opacity: 0.35,
  },
  lockDate: { color: '#F3D9DE', fontSize: 17, fontWeight: '600' },
  lockTime: {
    color: '#F3D9DE',
    fontSize: 84,
    fontWeight: '700',
    letterSpacing: -2,
    marginTop: -4,
    opacity: 0.92,
  },
  lockRow: { flexDirection: 'row', gap: 10, marginTop: 2 },
  lockCaption: { color: '#D9BCC2', fontSize: 12, marginTop: 12, opacity: 0.8 },
  slot: {
    borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.07)',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  charCard: {
    backgroundColor: C.card,
    borderRadius: 18,
    paddingVertical: 12,
    paddingHorizontal: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: C.line,
  },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: C.card,
    borderWidth: 1,
    borderColor: C.line,
  },
  selected: { backgroundColor: C.cardHi, borderColor: C.accent },
  chipText: { color: C.dim, fontSize: 15, fontWeight: '600' },
  badge: {
    color: C.bg,
    backgroundColor: C.accent,
    fontSize: 11,
    fontWeight: '800',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 6,
    overflow: 'hidden',
  },
  card: { backgroundColor: C.card, borderRadius: 18, padding: 16, borderWidth: 1, borderColor: C.line },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 7 },
  body: { color: C.text, fontSize: 16, lineHeight: 22 },
  dim: { color: C.dim, fontSize: 13, lineHeight: 18 },
  stepNum: {
    color: C.bg,
    backgroundColor: C.accent,
    width: 22,
    height: 22,
    borderRadius: 11,
    textAlign: 'center',
    lineHeight: 22,
    fontWeight: '800',
    overflow: 'hidden',
  },
});
