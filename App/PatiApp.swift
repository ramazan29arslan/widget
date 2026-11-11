import SwiftUI
import WidgetKit

@main
struct PatiApp: App {
    @Environment(\.scenePhase) private var scenePhase

    init() {
        FontRegistry.registerAll()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                // Widget pil okuyamazsa diye son bilgiyi paylaşılan alana yaz.
                BatteryReader.saveCurrent()
                WidgetCenter.shared.reloadAllTimelines()
            }
        }
    }
}
