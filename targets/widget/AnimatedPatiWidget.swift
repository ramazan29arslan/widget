import SwiftUI
import WidgetKit

struct AnimatedEntry: TimelineEntry {
    let date: Date
    let character: PatiCharacter
    let clip: AnimationClip
    let mood: Mood
    /// Sayacın saydığı başlangıç anı. Günün başı seçilir; değeri önemli değil,
    /// yeter ki saniyeler ilerlesin.
    let anchor: Date
}

struct AnimatedProvider: AppIntentTimelineProvider {
    func placeholder(in context: Context) -> AnimatedEntry {
        makeEntry(date: .now, intent: AnimatedPatiIntent(), battery: (nil, false))
    }

    func snapshot(for configuration: AnimatedPatiIntent, in context: Context) async -> AnimatedEntry {
        let battery = await BatteryReader.read()
        return makeEntry(date: .now, intent: configuration, battery: battery)
    }

    func timeline(for configuration: AnimatedPatiIntent, in context: Context) async -> Timeline<AnimatedEntry> {
        let battery = await BatteryReader.read()
        let now = Date()
        // Animasyonu sistem sayacı yürütür; timeline yalnızca "otomatik" modda
        // klibi ruh haline göre değiştirmek için 30 dakikada bir kayıt içerir.
        let entries = (0..<8).map { step in
            makeEntry(date: now.addingTimeInterval(Double(step) * 30 * 60),
                      intent: configuration, battery: battery)
        }
        return Timeline(entries: entries, policy: .atEnd)
    }

    private func makeEntry(date: Date,
                           intent: AnimatedPatiIntent,
                           battery: (level: Float?, charging: Bool)) -> AnimatedEntry {
        let character = CharacterCatalog.character(intent.character?.id)
        let mood = MoodEngine.mood(
            for: MoodInputs(date: date, batteryLevel: battery.level, isCharging: battery.charging),
            reactToBattery: SharedSettings.reactToBattery)
        let requested = intent.animation?.id ?? AnimationEntity.autoID
        let clipID = requested == AnimationEntity.autoID ? mood.preferredClipID : requested
        return AnimatedEntry(date: date,
                             character: character,
                             clip: character.clip(clipID),
                             mood: mood,
                             anchor: Calendar.current.startOfDay(for: date))
    }
}

struct AnimatedPatiView: View {
    let entry: AnimatedEntry

    var body: some View {
        GlyphView(fontName: entry.clip.fontName, content: .animation(anchor: entry.anchor))
            .widgetAccentable()
            .containerBackground(for: .widget) { Color.clear }
    }
}

struct AnimatedPatiWidget: Widget {
    let kind = "AnimatedPati"

    var body: some WidgetConfiguration {
        AppIntentConfiguration(kind: kind,
                               intent: AnimatedPatiIntent.self,
                               provider: AnimatedProvider()) { entry in
            AnimatedPatiView(entry: entry)
        }
        .configurationDisplayName("Canlı Pati")
        .description("Saniyede bir kare: kuyruk sallar, yürür, nefes alır.")
        .supportedFamilies([.accessoryRectangular, .accessoryCircular, .systemSmall])
    }
}

#Preview(as: .accessoryRectangular) {
    AnimatedPatiWidget()
} timeline: {
    let cat = CharacterCatalog.all[0]
    AnimatedEntry(date: .now, character: cat, clip: cat.clip("tail"),
                  mood: .awake, anchor: Calendar.current.startOfDay(for: .now))
    AnimatedEntry(date: .now, character: cat, clip: cat.clip("walk"),
                  mood: .playful, anchor: Calendar.current.startOfDay(for: .now))
}
