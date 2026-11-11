import SwiftUI
import WidgetKit

struct ContentView: View {
    var body: some View {
        NavigationStack {
            List {
                Section("Karakterler") {
                    ForEach(CharacterCatalog.all) { character in
                        NavigationLink(value: character) {
                            HStack(spacing: 16) {
                                GlyphView(fontName: character.clips[0].fontName,
                                          content: .animation(anchor: .startOfToday))
                                    .frame(width: 96, height: 52)
                                Text(character.name).font(.headline)
                            }
                        }
                    }
                }
                Section {
                    SettingsSection()
                }
                Section("Widget nasıl eklenir?") {
                    Text("Kilit ekranına basılı tut → Özelleştir → Kilit Ekranı → saatin altındaki alana dokun → Pati'yi seç.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Pati")
            .navigationDestination(for: PatiCharacter.self) { CharacterDetailView(character: $0) }
        }
    }
}

struct CharacterDetailView: View {
    let character: PatiCharacter

    var body: some View {
        List {
            Section("Animasyonlar (saniyede 1 kare)") {
                ForEach(character.clips) { clip in
                    VStack(alignment: .leading, spacing: 8) {
                        Text(clip.title).font(.subheadline.weight(.semibold))
                        LockScreenPreview {
                            GlyphView(fontName: clip.fontName, content: .animation(anchor: .startOfToday))
                        }
                    }
                    .padding(.vertical, 4)
                }
            }
            Section("Ruh hali pozları") {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 140))], spacing: 12) {
                    ForEach(Mood.allCases, id: \.self) { mood in
                        VStack(spacing: 6) {
                            LockScreenPreview {
                                GlyphView(fontName: character.poseFontName,
                                          content: .pose(character.poseLetter(for: mood)))
                            }
                            Text(mood.title).font(.caption)
                        }
                    }
                }
                .padding(.vertical, 6)
            }
        }
        .navigationTitle(character.name)
    }
}

/// Kilit ekranındaki dikdörtgen widget boyutunda koyu bir önizleme kutusu.
struct LockScreenPreview<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        content
            .foregroundStyle(.white.opacity(0.9))
            .frame(width: 158, height: 72)
            .background(Color(red: 0.2, green: 0.08, blue: 0.12), in: RoundedRectangle(cornerRadius: 14))
    }
}

struct SettingsSection: View {
    @State private var reactToBattery = SharedSettings.reactToBattery
    @State private var mood: Mood = .awake

    var body: some View {
        Toggle("Şarja tepki ver", isOn: $reactToBattery)
            .onChange(of: reactToBattery) { _, value in
                SharedSettings.reactToBattery = value
                WidgetCenter.shared.reloadAllTimelines()
                refreshMood()
            }
        LabeledContent("Şu anki ruh hali", value: mood.title)
            .onAppear(perform: refreshMood)
        Button("Widget'ları yenile") {
            BatteryReader.saveCurrent()
            WidgetCenter.shared.reloadAllTimelines()
            refreshMood()
        }
    }

    private func refreshMood() {
        let battery = BatteryReader.read()
        mood = MoodEngine.mood(
            for: MoodInputs(date: .now, batteryLevel: battery.level, isCharging: battery.charging),
            reactToBattery: reactToBattery)
    }
}

extension Date {
    static var startOfToday: Date { Calendar.current.startOfDay(for: .now) }
}

#Preview {
    ContentView()
}
