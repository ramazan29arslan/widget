import SwiftUI

/// Bir karakter karesini (glif) verilen alana sığdırarak çizer.
/// Glifler 2:1 oranlıdır (2000 × 1000 font birimi).
struct GlyphView: View {
    enum Content {
        /// Saniyede bir kare ilerleyen animasyon.
        case animation(anchor: Date)
        /// Sabit poz harfi.
        case pose(String)
    }

    let fontName: String
    let content: Content

    var body: some View {
        GeometryReader { geo in
            let size = max(1, min(geo.size.width / 2.0, geo.size.height / 1.1))
            label
                .font(.custom(fontName, fixedSize: size))
                .lineLimit(1)
                .multilineTextAlignment(.center)
                .frame(width: geo.size.width, height: geo.size.height)
        }
    }

    @ViewBuilder
    private var label: some View {
        switch content {
        case .animation(let anchor):
            // Sistem sayacı "1:23:45" yazar; font yalnızca son haneyi kare olarak gösterir.
            Text(anchor, style: .timer)
        case .pose(let letter):
            Text(letter)
        }
    }
}
