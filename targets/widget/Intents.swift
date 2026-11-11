import AppIntents
import WidgetKit

// MARK: - Karakter seçimi

struct CharacterEntity: AppEntity {
    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Karakter"
    static let defaultQuery = CharacterQuery()

    let id: String
    let name: String

    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(title: "\(name)")
    }

    init(_ character: PatiCharacter) {
        id = character.id
        name = character.name
    }
}

struct CharacterQuery: EntityQuery {
    func entities(for identifiers: [String]) async throws -> [CharacterEntity] {
        CharacterCatalog.all.filter { identifiers.contains($0.id) }.map(CharacterEntity.init)
    }

    func suggestedEntities() async throws -> [CharacterEntity] {
        CharacterCatalog.all.map(CharacterEntity.init)
    }

    func defaultResult() async -> CharacterEntity? {
        CharacterCatalog.all.first.map(CharacterEntity.init)
    }
}

// MARK: - Animasyon seçimi

struct AnimationEntity: AppEntity {
    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Animasyon"
    static let defaultQuery = AnimationQuery()
    static let autoID = "auto"

    let id: String
    let title: String

    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(title: "\(title)")
    }

    static var all: [AnimationEntity] {
        [AnimationEntity(id: autoID, title: "Otomatik (ruh haline göre)")]
            + CharacterCatalog.allClips.map { AnimationEntity(id: $0.id, title: $0.title) }
    }
}

struct AnimationQuery: EntityQuery {
    func entities(for identifiers: [String]) async throws -> [AnimationEntity] {
        AnimationEntity.all.filter { identifiers.contains($0.id) }
    }

    func suggestedEntities() async throws -> [AnimationEntity] {
        AnimationEntity.all
    }

    func defaultResult() async -> AnimationEntity? {
        AnimationEntity.all.first
    }
}

// MARK: - Widget ayarları

struct AnimatedPatiIntent: WidgetConfigurationIntent {
    static let title: LocalizedStringResource = "Canlı Pati"
    static let description = IntentDescription("Saniyede bir kare oynayan karakter.")

    @Parameter(title: "Karakter")
    var character: CharacterEntity?

    @Parameter(title: "Animasyon")
    var animation: AnimationEntity?
}

struct MoodPatiIntent: WidgetConfigurationIntent {
    static let title: LocalizedStringResource = "Ruh Hali Pati"
    static let description = IntentDescription("Saate ve şarja göre poz değiştiren karakter.")

    @Parameter(title: "Karakter")
    var character: CharacterEntity?
}
