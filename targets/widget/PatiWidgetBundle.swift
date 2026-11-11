import SwiftUI
import WidgetKit

@main
struct PatiWidgetBundle: WidgetBundle {
    init() {
        FontRegistry.registerAll()
    }

    var body: some Widget {
        AnimatedPatiWidget()
        MoodPatiWidget()
    }
}
