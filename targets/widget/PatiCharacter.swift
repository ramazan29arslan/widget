import Foundation

/// 10 karelik bir animasyon klibi. Her klip ayrı bir fonttur:
/// sayaç metninin son hanesi (0-9) o anki kareyi seçer.
/// Panorama klipleri iki widget'a yayılır: sol ve sağ yarı ayrı fontlardır.
struct AnimationClip: Hashable, Identifiable {
    let id: String
    let title: String
    /// Tek widget için font (panoramada küçültülmüş tam sahne).
    let fontName: String
    let leftFont: String?
    let rightFont: String?

    var isWide: Bool { leftFont != nil }

    func font(for part: WidgetPart) -> String {
        switch part {
        case .full: return fontName
        case .left: return leftFont ?? fontName
        case .right: return rightFont ?? fontName
        }
    }
}

/// Kilit ekranında widget'ın panoramadaki yeri.
enum WidgetPart: String, CaseIterable {
    case full, left, right
}

/// Bir karakter paketi: animasyon klipleri + ruh hali pozları.
struct PatiCharacter: Hashable, Identifiable {
    let id: String
    let name: String
    let clips: [AnimationClip]
    let poseFontName: String
    let poses: [String]
    /// Ruh hali -> "Otomatik" modda oynatılacak klip.
    let moodClips: [String: String]

    func clip(_ id: String?) -> AnimationClip {
        clips.first { $0.id == id } ?? clips[0]
    }

    /// Ruh haline ve widget'ın yerine göre oynatılacak klip.
    /// requested nil ise "Otomatik": ruh haline uyan klip seçilir.
    func clip(for mood: Mood, part: WidgetPart, requested: String?) -> AnimationClip {
        var chosen = clip(requested ?? moodClips[mood.rawValue])
        // Panorama parçasında dar bir klip iki widget'ta aynı sahneyi gösterirdi;
        // önce ruh haline uyan, yoksa ilk panorama klibine geç.
        if part != .full, !chosen.isWide {
            let moodClip = clip(moodClips[mood.rawValue])
            chosen = moodClip.isWide ? moodClip : (clips.first(where: \.isWide) ?? chosen)
        }
        return chosen
    }

    func poseLetter(for mood: Mood) -> String {
        poses.contains(mood.poseLetter) ? mood.poseLetter : (poses.first ?? "a")
    }
}

/// Karakter listesi `CharacterCatalog.generated.swift` içinde üretilir.
enum CharacterCatalog {
    static func character(_ id: String?) -> PatiCharacter {
        all.first { $0.id == id } ?? all[0]
    }

    /// Tüm karakterlerdeki benzersiz klipler (widget ayarları için).
    static var allClips: [AnimationClip] {
        var seen = Set<String>()
        return all.flatMap(\.clips).filter { seen.insert($0.id).inserted }
    }
}
