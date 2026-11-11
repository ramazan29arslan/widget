import Foundation

/// Karakterin ruh hali. Saat, şarj ve şarj durumuna göre hesaplanır.
enum Mood: String, CaseIterable, Codable {
    case awake, sleepy, sleeping, tired, playful

    /// Poz fontundaki harf.
    var poseLetter: String {
        switch self {
        case .awake: return "a"
        case .sleepy: return "s"
        case .sleeping: return "z"
        case .tired: return "t"
        case .playful: return "p"
        }
    }

    var title: String {
        switch self {
        case .awake: return "Uyanık"
        case .sleepy: return "Uykulu"
        case .sleeping: return "Uyuyor"
        case .tired: return "Yorgun"
        case .playful: return "Oyuncu"
        }
    }

    /// "Otomatik" animasyon seçiliyken bu ruh haline uyan klip.
    var preferredClipID: String {
        switch self {
        case .awake: return "tail"
        case .sleepy, .sleeping, .tired: return "breathe"
        case .playful: return "roll"
        }
    }
}

struct MoodInputs {
    var date: Date
    var batteryLevel: Float?   // 0...1, bilinmiyorsa nil
    var isCharging: Bool
}

enum MoodEngine {
    static func mood(for input: MoodInputs,
                     reactToBattery: Bool,
                     calendar: Calendar = .current) -> Mood {
        if reactToBattery {
            if let level = input.batteryLevel, level < 0.2, !input.isCharging {
                return .tired            // şarj azaldı: yere serilir
            }
            if input.isCharging {
                return .sleeping         // şarjdayken şekerleme
            }
        }
        let hour = calendar.component(.hour, from: input.date)
        switch hour {
        case 0..<6: return .sleeping
        case 6..<8: return .sleepy       // sabah mahmurluğu
        case 13..<15: return .sleepy     // öğle uykusu
        case 17..<20: return .playful    // akşam oyun saati
        case 22..<24: return .sleepy
        default: return .awake
        }
    }
}
