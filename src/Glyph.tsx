import { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ViewStyle } from 'react-native';

/** Her saniye değişen kare numarası (0-9). Widget'taki sayaçla aynı: saniye % 10. */
export function useFrame(): number {
  const [frame, setFrame] = useState(() => new Date().getSeconds() % 10);
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    // Saniye başına hizala, sonra her saniye ilerle.
    const timeout = setTimeout(() => {
      setFrame(new Date().getSeconds() % 10);
      interval = setInterval(() => setFrame(new Date().getSeconds() % 10), 1000);
    }, 1000 - new Date().getMilliseconds());
    return () => {
      clearTimeout(timeout);
      if (interval) clearInterval(interval);
    };
  }, []);
  return frame;
}

type Props = {
  fontName: string;
  /** Pozlar için harf; verilmezse animasyon kareleri oynar. */
  letter?: string;
  width: number;
  color?: string;
  style?: ViewStyle;
};

/** Karakter glifini çizer. Glifler 2:1 oranlıdır (2000 × 1000 font birimi). */
export function Glyph({ fontName, letter, width, color = '#F6DEE4', style }: Props) {
  return (
    <View style={[{ width, height: width / 2 + 4, alignItems: 'center', justifyContent: 'flex-end' }, style]}>
      {letter !== undefined ? (
        <GlyphText fontName={fontName} text={letter} width={width} color={color} />
      ) : (
        <AnimatedGlyph fontName={fontName} width={width} color={color} />
      )}
    </View>
  );
}

function AnimatedGlyph({ fontName, width, color }: { fontName: string; width: number; color: string }) {
  const frame = useFrame();
  return <GlyphText fontName={fontName} text={String(frame)} width={width} color={color} />;
}

function GlyphText({ fontName, text, width, color }: { fontName: string; text: string; width: number; color: string }) {
  const size = width / 2;
  return (
    <Text
      allowFontScaling={false}
      style={[styles.text, { fontFamily: fontName, fontSize: size, lineHeight: size * 1.1, color }]}
    >
      {text}
    </Text>
  );
}

const styles = StyleSheet.create({
  text: { includeFontPadding: false },
});
