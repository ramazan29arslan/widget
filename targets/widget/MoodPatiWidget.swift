import SwiftUI
import WidgetKit

struct MoodEntry: TimelineEntry {
    let date: Date
    let character: PatiCharacter
    let mood: Mood
}

struct MoodProvider: AppIntentTimelineProvider {
    func placeholder(in context: Context) -> MoodEntry {
        MoodEntry(date: .now, character: CharacterCatalog.all[0], mood: .awake)
    }

    func snapshot(for configuration: MoodPatiIntent, in context: Context) async -> MoodEntry {
        let battery = await BatteryReader.read()
        return entry(at: .now, configuration, battery)
    }

    func timeline(for configuration: MoodPatiIntent, in context: Context) async -> Timeline<MoodEntry> {
        let battery = await BatteryReader.read()
        let now = Date()
        // Saate bağlı pozlar önceden hesaplanır (15 dk aralıkla 3 saat).
        // Pil yalnızca yenilemede okunur; 3 saat sonra yeni timeline istenir.
        let entries = (0..<12).map { step in
            entry(at: now.addingTimeInterval(Double(step) * 15 * 60), configuration, battery)
        }
        return Timeline(entries: entries, policy: .atEnd)
    }

    private func entry(at date: Date,
                       _ intent: MoodPatiIntent,
                       _ battery: (level: Float?, charging: Bool)) -> MoodEntry {
        let mood = MoodEngine.mood(
            for: MoodInputs(date: date, batteryLevel: battery.level, isCharging: battery.charging),
            reactToBattery: SharedSettings.reactToBattery)
        return MoodEntry(date: date, character: CharacterCatalog.character(intent.character?.id), mood: mood)
    }
}

struct MoodPatiView: View {
    let entry: MoodEntry

    var body: some View {
        GlyphView(fontName: entry.character.poseFontName,
                  content: .pose(entry.character.poseLetter(for: entry.mood)))
            .widgetAccentable()
            // iOS 17+: poz değişiminde yumuşak geçiş
            .contentTransition(.opacity)
            .containerBackground(for: .widget) { Color.clear }
    }
}

struct MoodPatiWidget: Widget {
    let kind = "MoodPati"

    var body: some WidgetConfiguration {
        AppIntentConfiguration(kind: kind,
                               intent: MoodPatiIntent.self,
                               provider: MoodProvider()) { entry in
            MoodPatiView(entry: entry)
        }
        .configurationDisplayName("Ruh Hali Pati")
        .description("Saate ve şarja göre uyanır, uyuklar, yere serilir.")
        .supportedFamilies([.accessoryRectangular, .accessoryCircular, .systemSmall])
    }
}

#Preview(as: .accessoryRectangular) {
    MoodPatiWidget()
} timeline: {
    let cat = CharacterCatalog.all[0]
    MoodEntry(date: .now, character: cat, mood: .awake)
    MoodEntry(date: .now, character: cat, mood: .sleepy)
    MoodEntry(date: .now, character: cat, mood: .sleeping)
    MoodEntry(date: .now, character: cat, mood: .tired)
    MoodEntry(date: .now, character: cat, mood: .playful)
}
