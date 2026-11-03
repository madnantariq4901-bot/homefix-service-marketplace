import os

from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from app.core.security import hash_password
from app.database.models import (
    CategoryName,
    Job,
    JobStatus,
    ProviderProfile,
    ProviderSkill,
    Quote,
    Review,
    ServiceCategory,
    User,
    UserRole,
)
from app.database.session import SessionLocal


CATEGORIES = [
    (CategoryName.PLUMBER, 600.0, "Leak repair, tap and pipe fitting, bathroom and kitchen plumbing, water tank and motor work"),
    (CategoryName.ELECTRICIAN, 700.0, "House wiring, switches and sockets, fan and light fitting, breaker and meter board repair"),
    (CategoryName.CARPENTER, 800.0, "Doors, windows, cupboards, wardrobes, furniture repair and custom woodwork"),
    (CategoryName.MECHANIC, 900.0, "Car and bike diagnostics, engine and brake repair, oil change and general servicing"),
    (CategoryName.AC_TECHNICIAN, 1000.0, "AC installation, gas filling, servicing, repair and uninstall"),
    (CategoryName.PAINTER, 700.0, "Interior and exterior painting, polish, wall putty and touch-ups"),
    (CategoryName.CLEANER, 500.0, "Home, office and deep cleaning, sofa and carpet cleaning, water tank cleaning"),
    (CategoryName.MASON, 900.0, "Brickwork, plaster, tiles, flooring and small construction repairs"),
]


def _get_or_create_category(db: Session, name: CategoryName, rate: float, description: str) -> ServiceCategory:
    category = db.query(ServiceCategory).filter(ServiceCategory.name == name).first()
    if category is None:
        category = ServiceCategory(name=name, base_hourly_rate=rate, description=description)
        db.add(category)
        db.commit()
        db.refresh(category)
    return category


def _get_or_create_user(
    db: Session,
    email: str,
    full_name: str,
    role: UserRole,
    password: str,
) -> User:
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if user is None:
        user = User(
            email=normalized_email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _get_or_create_demo_provider_user(
    db: Session,
    legacy_email: str,
    email: str,
    full_name: str,
    password: str,
) -> User:
    normalized_email = email.strip().lower()
    legacy_user = db.query(User).filter(User.email == legacy_email).first()
    current_user = db.query(User).filter(User.email == normalized_email).first()

    if legacy_user is not None and current_user is not None:
        raise RuntimeError(
            f"Cannot migrate demo provider {legacy_email}: {normalized_email} is already registered"
        )
    if legacy_user is not None:
        legacy_user.email = normalized_email
        db.commit()
        db.refresh(legacy_user)
        return legacy_user
    return _get_or_create_user(db, normalized_email, full_name, UserRole.PROVIDER, password)


def _get_or_create_provider(db: Session, user: User, *, name: str, lat: float | None, lng: float | None) -> ProviderProfile:
    profile = db.query(ProviderProfile).filter(ProviderProfile.user_id == user.id).first()
    if profile is None:
        profile = ProviderProfile(
            user_id=user.id,
            is_verified=True,
            is_available=True,
            current_lat=lat,
            current_lng=lng,
            rating_avg=4.4,
            rating_count=2,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    else:
        profile.is_verified = True
        profile.is_available = True
        if lat is not None:
            profile.current_lat = lat
        if lng is not None:
            profile.current_lng = lng
        if profile.rating_count == 0:
            profile.rating_avg = 4.5
            profile.rating_count = 1
    return profile


def _ensure_skill(db: Session, provider: ProviderProfile, category: ServiceCategory, years_experience: int) -> None:
    existing = (
        db.query(ProviderSkill)
        .filter(ProviderSkill.provider_id == provider.id, ProviderSkill.category_id == category.id)
        .first()
    )
    if existing is None:
        db.add(
            ProviderSkill(
                provider_id=provider.id,
                category_id=category.id,
                years_experience=years_experience,
            )
        )
    else:
        existing.years_experience = years_experience


def _get_or_create_job(
    db: Session,
    *,
    customer: User,
    provider: ProviderProfile | None,
    category: ServiceCategory,
    description: str,
    address: str,
    lat: float | None,
    lng: float | None,
    status: JobStatus,
    quoted_amount: float | None = None,
    final_amount: float | None = None,
) -> Job:
    existing = (
        db.query(Job)
        .filter(Job.customer_id == customer.id, Job.address == address, Job.description == description)
        .first()
    )
    if existing is not None:
        return existing

    job = Job(
        customer_id=customer.id,
        provider_id=provider.id if provider else None,
        category_id=category.id,
        description=description,
        address=address,
        lat=lat,
        lng=lng,
        status=status,
        quoted_amount=quoted_amount,
        final_amount=final_amount,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _get_or_create_quote(db: Session, job: Job, provider: ProviderProfile, quoted_amount: float) -> Quote:
    existing = db.query(Quote).filter(Quote.job_id == job.id, Quote.provider_id == provider.id).first()
    if existing is None:
        existing = Quote(job_id=job.id, provider_id=provider.id, quoted_amount=quoted_amount)
        db.add(existing)
        db.commit()
        db.refresh(existing)
    else:
        existing.quoted_amount = quoted_amount
    return existing


def _ensure_review(db: Session, job: Job, customer: User, provider: ProviderProfile, rating: int, comment: str) -> Review:
    existing = db.query(Review).filter(Review.job_id == job.id).first()
    if existing is not None:
        return existing

    review = Review(
        job_id=job.id,
        customer_id=customer.id,
        provider_id=provider.id,
        rating=rating,
        comment=comment,
    )
    db.add(review)
    previous_count = provider.rating_count
    provider.rating_count = previous_count + 1
    provider.rating_avg = round(((provider.rating_avg * previous_count) + rating) / provider.rating_count, 2)
    db.commit()
    db.refresh(review)
    return review


def seed(db: Session) -> None:
    for name, rate, description in CATEGORIES:
        _get_or_create_category(db, name, rate, description)

    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    if admin_email and admin_password:
        _get_or_create_user(db, admin_email, os.getenv("ADMIN_FULL_NAME", "Administrator"), UserRole.ADMIN, admin_password)

    demo_customer_password = "DemoCustomer123"
    customer_1 = _get_or_create_user(db, "customer1@example.com", "Ayesha Khan", UserRole.CUSTOMER, demo_customer_password)
    customer_2 = _get_or_create_user(db, "customer2@example.com", "Saad Malik", UserRole.CUSTOMER, demo_customer_password)

    demo_provider_password = "DemoProvider123"
    provider_1 = _get_or_create_demo_provider_user(
        db, "plumber@demo.local", "plumber@example.com", "Ali Raza", demo_provider_password
    )
    provider_2 = _get_or_create_demo_provider_user(
        db, "electrician@demo.local", "electrician@example.com", "Nadia Qureshi", demo_provider_password
    )
    provider_3 = _get_or_create_demo_provider_user(
        db, "cleaner@demo.local", "cleaner@example.com", "Maryam Hassan", demo_provider_password
    )

    service_categories = {category.name: category for category in db.query(ServiceCategory).all()}

    profile_1 = _get_or_create_provider(db, provider_1, name="Ali Raza", lat=31.5204, lng=74.3587)
    profile_2 = _get_or_create_provider(db, provider_2, name="Nadia Qureshi", lat=31.4504, lng=74.2714)
    profile_3 = _get_or_create_provider(db, provider_3, name="Maryam Hassan", lat=31.4837, lng=74.3401)

    _ensure_skill(db, profile_1, service_categories[CategoryName.PLUMBER], 6)
    _ensure_skill(db, profile_2, service_categories[CategoryName.ELECTRICIAN], 8)
    _ensure_skill(db, profile_3, service_categories[CategoryName.CLEANER], 5)
    _ensure_skill(db, profile_1, service_categories[CategoryName.MASON], 4)

    _get_or_create_job(
        db,
        customer=customer_2,
        provider=None,
        category=service_categories[CategoryName.PLUMBER],
        description="Demo request: repair a leaking kitchen tap.",
        address="Near Model Town, Lahore",
        lat=31.4890,
        lng=74.3020,
        status=JobStatus.REQUESTED,
    )
    _get_or_create_job(
        db,
        customer=customer_1,
        provider=None,
        category=service_categories[CategoryName.ELECTRICIAN],
        description="Demo request: install two ceiling lights.",
        address="Near Gulberg, Lahore",
        lat=31.5150,
        lng=74.3350,
        status=JobStatus.REQUESTED,
    )
    _get_or_create_job(
        db,
        customer=customer_2,
        provider=None,
        category=service_categories[CategoryName.CLEANER],
        description="Demo request: deep clean a two-bedroom apartment.",
        address="Near Johar Town, Lahore",
        lat=31.4700,
        lng=74.2800,
        status=JobStatus.REQUESTED,
    )

    job_1 = _get_or_create_job(
        db,
        customer=customer_1,
        provider=profile_1,
        category=service_categories[CategoryName.PLUMBER],
        description="Kitchen sink leaking under cabinet and need new tap installation.",
        address="Model Town, Lahore",
        lat=31.4801,
        lng=74.2997,
        status=JobStatus.REQUESTED,
    )
    if job_1.status == JobStatus.REQUESTED:
        _get_or_create_quote(db, job_1, profile_1, 1600.0)

    job_2 = _get_or_create_job(
        db,
        customer=customer_2,
        provider=profile_2,
        category=service_categories[CategoryName.ELECTRICIAN],
        description="Light fixtures and backup power wiring for a duplex apartment.",
        address="Gulberg, Lahore",
        lat=31.5136,
        lng=74.3338,
        status=JobStatus.ACCEPTED,
        quoted_amount=2200.0,
        final_amount=2050.0,
    )
    _get_or_create_quote(db, job_2, profile_2, 2200.0)

    job_3 = _get_or_create_job(
        db,
        customer=customer_1,
        provider=profile_3,
        category=service_categories[CategoryName.CLEANER],
        description="Deep cleaning of 3-bedroom home including kitchen and windows.",
        address="Johar Town, Lahore",
        lat=31.4682,
        lng=74.2797,
        status=JobStatus.COMPLETED,
        quoted_amount=3500.0,
        final_amount=3200.0,
    )
    _ensure_review(db, job_3, customer_1, profile_3, 5, "Excellent work and very thorough cleaning.")

    job_4 = _get_or_create_job(
        db,
        customer=customer_2,
        provider=profile_1,
        category=service_categories[CategoryName.MASON],
        description="Wall tile replacement and bathroom repair around shower area.",
        address="DHA, Lahore",
        lat=31.4971,
        lng=74.3810,
        status=JobStatus.COMPLETED,
        quoted_amount=4700.0,
        final_amount=4550.0,
    )
    _ensure_review(db, job_4, customer_2, profile_1, 4, "Good craftsmanship and on-time completion.")

    db.commit()


def _main() -> None:
    with SessionLocal() as session:
        seed(session)
    print("Seed complete")


if __name__ == "__main__":
    _main()
