import Foundation

/// 10 karelik bir animasyon klibi. Her klip ayrı bir fonttur:
/// sayaç metninin son hanesi (0-9) o anki kareyi seçer.
struct AnimationClip: Hashable, Identifiable {
    let id: String
    let title: String
    let fontName: String
}

/// Bir karakter paketi: animasyon klipleri + ruh hali pozları.
struct PatiCharacter: Hashable, Identifiable {
    let id: String
    let name: String
    let clips: [AnimationClip]
    /// Pozların bulunduğu font. Her poz bir harftir (bkz. Mood.poseLetter).
    let poseFontName: String
    let poses: [String]

    func clip(_ id: String?) -> AnimationClip {
        clips.first { $0.id == id } ?? clips[0]
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
