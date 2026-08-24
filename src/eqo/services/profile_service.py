from eqo.domain.user import UserProfile
from eqo.storage.repositories import UserProfileRepository


class ProfileService:
    def __init__(self, repository: UserProfileRepository) -> None:
        self.repository = repository

    def current(self) -> UserProfile | None:
        return self.repository.get()

    def save(self, profile: UserProfile) -> UserProfile:
        self.repository.save(profile)
        return profile

    def change_assistant_name(self, name: str) -> UserProfile:
        profile = self.current()
        if profile is None:
            raise LookupError("O onboarding ainda não foi concluído.")
        updated = profile.with_assistant_name(name)
        self.repository.save(updated)
        return updated
