# Domain-Driven Design in Intric

## TLDR
- **Feature Organization**: Domain entities, repositories, services, and factories
- **Implementation Pattern**: Follow the standard structure in `feature_x/` directories
- **Business Logic**: Keep domain logic in entities, cross-entity operations in services
- **Testing Approach**: Write domain tests, application tests, and integration tests
- **Development Flow**: Model the domain first, then implement the technical components

This document outlines how Domain-Driven Design (DDD) principles are applied within the Intric platform, particularly for new feature development.

## Table of Contents
- [Introduction to DDD](#introduction-to-ddd)
- [Core DDD Concepts](#core-ddd-concepts)
- [Implementation in Intric](#implementation-in-intric)
- [Feature Structure](#feature-structure)
- [Development Guidelines](#development-guidelines)
- [Example Implementation](#example-implementation)
- [Common Patterns](#common-patterns)
- [Testing Approach](#testing-approach)

## Introduction to DDD

Domain-Driven Design is an approach to software development that focuses on creating a rich domain model that reflects the business processes and requirements. It prioritizes:

- Understanding the core business domain
- Collaboration between technical and domain experts
- Creating a ubiquitous language shared by all team members
- Focusing on the core domain and domain logic
- Maintaining a model-driven design

In Intric, we apply DDD principles to ensure our codebase directly reflects the business domain of AI-powered knowledge management systems.

## Core DDD Concepts

### Ubiquitous Language

A shared language between developers and domain experts that is used consistently in:
- Code (class and method names)
- Documentation
- Conversations

### Bounded Contexts

Explicit boundaries within which a particular domain model applies:
- Each bounded context has its own ubiquitous language
- Models across contexts may differ even for the same concept
- Contexts are integrated through defined relationships

### Entities and Value Objects

- **Entities**: Objects defined by their identity (e.g., Assistants, Spaces)
- **Value Objects**: Immutable objects defined by their attributes (e.g., Embedding, Prompt)

### Aggregates

Clusters of domain objects treated as a single unit:
- Each aggregate has a root entity
- External references are only to the aggregate root
- Changes within the aggregate maintain consistency rules

### Repositories

Objects that provide collection-like access to aggregates:
- Abstract the underlying persistence mechanism
- Provide methods to find and save aggregates

### Domain Services

Stateless operations that don't naturally belong to entities or value objects:
- Operate on multiple aggregates
- Implement complex domain processes

## Implementation in Intric

In Intric, we implement DDD with a focus on maintainability and clarity:

### Domain Layer

The core domain layer contains:
- Domain entities and value objects
- Domain services
- Repository interfaces
- Domain events

### Application Layer

Coordinates domain objects to perform application tasks:
- Application services orchestrate domain objects
- DTOs for transferring data
- Event handlers for domain events

### Infrastructure Layer

Implements technical concerns:
- Repository implementations
- External system integrations
- Persistence mechanisms
- Messaging systems

### Interface Layer

Handles interaction with external systems:
- API endpoints
- User interface components
- External service adapters

## Feature Structure

For new features in Intric, we follow this standard structure:

```
feature_x/
├── api/                         # API layer (may also be named 'presentation/')
│   ├── feature_x_models.py      # API schema definitions
│   ├── feature_x_assembler.py   # Translates domain objects to API schema
│   └── feature_x_router.py      # API endpoints and routes
├── feature_x.py                 # Main domain entity/object
├── feature_x_repo.py            # Repository for persistence
├── feature_x_service.py         # Domain service layer
└── feature_x_factory.py         # Factory for creating domain objects
```

> **Note**: Some features use `api/` for the interface layer while others use `presentation/`. Both follow the same pattern of separating API concerns from domain logic.

### Component Responsibilities

#### Domain Entity (`feature_x.py`)

The main domain object containing business logic:

```python
class Space:
    def __init__(self, id: str, name: str, owner_id: str):
        self.id = id
        self.name = name
        self.owner_id = owner_id
        self._members = []
        
    def add_member(self, user_id: str, role: str) -> None:
        """Add a member to the space with the specified role."""
        if self._is_member(user_id):
            raise DomainError("User is already a member of this space")
        
        self._members.append({"user_id": user_id, "role": role})
        
    def _is_member(self, user_id: str) -> bool:
        """Check if a user is a member of this space."""
        return any(member["user_id"] == user_id for member in self._members)
        
    def can_access(self, user_id: str) -> bool:
        """Determine if a user can access this space."""
        return user_id == self.owner_id or self._is_member(user_id)
```

#### Repository (`feature_x_repo.py`)

Abstracts data persistence operations:

```python
class SpaceRepository:
    def __init__(self, db_session):
        self.db_session = db_session
        
    def get_by_id(self, space_id: str) -> Optional<Space]:
        """Retrieve a space by its ID."""
        space_data = self.db_session.query(SpaceModel).filter_by(id=space_id).first()
        if not space_data:
            return None
        
        return self._map_to_domain(space_data)
        
    def save(self, space: Space) -> Space:
        """Save a space to the database."""
        space_model = self._map_to_model(space)
        self.db_session.merge(space_model)
        self.db_session.commit()
        return space
        
    def _map_to_domain(self, model: SpaceModel) -> Space:
        """Map database model to domain object."""
        space = Space(
            id=model.id,
            name=model.name,
            owner_id=model.owner_id
        )
        # Add members...
        return space
        
    def _map_to_model(self, space: Space) -> SpaceModel:
        """Map domain object to database model."""
        # Implementation...
```

#### Service (`feature_x_service.py`)

Coordinates domain objects and implements use cases:

```python
class SpaceService:
    def __init__(self, space_repo: SpaceRepository, user_service: UserService):
        self.space_repo = space_repo
        self.user_service = user_service
        
    def create_space(self, name: str, owner_id: str) -> Space:
        """Create a new space."""
        # Validate owner exists
        user = self.user_service.get_user(owner_id)
        if not user:
            raise ApplicationError("Owner user does not exist")
            
        # Create space
        space_id = str(uuid.uuid4())
        space = Space(id=space_id, name=name, owner_id=owner_id)
        
        # Save and return
        return self.space_repo.save(space)
        
    def add_member(self, space_id: str, user_id: str, role: str) -> Space:
        """Add a member to a space."""
        space = self.space_repo.get_by_id(space_id)
        if not space:
            raise ApplicationError("Space not found")
            
        user = self.user_service.get_user(user_id)
        if not user:
            raise ApplicationError("User not found")
            
        space.add_member(user_id, role)
        return self.space_repo.save(space)
```

#### Factory (`feature_x_factory.py`)

Creates properly initialized domain objects:

```python
class SpaceFactory:
    @staticmethod
    def create_space(name: str, owner_id: str) -> Space:
        """Create a new space with default settings."""
        space_id = str(uuid.uuid4())
        return Space(id=space_id, name=name, owner_id=owner_id)
        
    @staticmethod
    def create_from_dto(dto: SpaceDTO) -> Space:
        """Create a space from a DTO."""
        space = Space(
            id=dto.id or str(uuid.uuid4()),
            name=dto.name,
            owner_id=dto.owner_id
        )
        
        # Add members from DTO
        for member in dto.members:
            space.add_member(member.user_id, member.role)
            
        return space
```

#### API Layer (`api/feature_x_*.py`)

Handles HTTP concerns and data transformation:

```python
# feature_x_models.py - API models using Pydantic
class SpaceCreate(BaseModel):
    name: str
    
class SpaceMember(BaseModel):
    user_id: str
    role: str
    
class SpaceResponse(BaseModel):
    id: str
    name: str
    owner_id: str
    members: List[SpaceMember]
    created_at: datetime

# feature_x_assembler.py - Transforms between domain and API models
class SpaceAssembler:
    @staticmethod
    def to_response(space: Space) -> SpaceResponse:
        """Convert domain object to API response."""
        return SpaceResponse(
            id=space.id,
            name=space.name,
            owner_id=space.owner_id,
            members=[SpaceMember(user_id=m.user_id, role=m.role) for m in space.members],
            created_at=space.created_at
        )

# feature_x_router.py - API endpoints
@router.post("/spaces", response_model=SpaceResponse)
def create_space(
    space_data: SpaceCreate,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
):
    """Create a new space."""
    space_service = container.space_service()
    space = space_service.create_space(space_data.name, current_user.id)
    return SpaceAssembler.to_response(space)
```

## Development Guidelines

When implementing new features using DDD in Intric:

### 1. Start with the Domain

- Identify the core concepts and their relationships
- Define the ubiquitous language
- Create the domain model before implementation

### 2. Follow Separation of Concerns

- Keep domain logic in domain objects
- Use services for operations spanning multiple aggregates
- Keep infrastructure concerns (like persistence) out of domain objects

### 3. Use Value Objects

- Use value objects for concepts defined by their attributes
- Make value objects immutable
- Consider using value objects for validation

### 4. Protect Aggregate Consistency

- Define clear aggregate boundaries
- Ensure that changes within an aggregate maintain invariants
- Only allow external references to the aggregate root

### 5. Use Domain Events

- Use domain events to communicate between aggregates
- Make domain events part of the ubiquitous language
- Keep events immutable and descriptive

## Example Implementation

Let's look at implementing a Knowledge Base feature using DDD principles:

```python
# knowledge_base.py - Domain entity
class KnowledgeBase:
    def __init__(self, id: str, name: str, owner_id: str):
        self.id = id
        self.name = name
        self.owner_id = owner_id
        self.sources = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
    def add_source(self, source: KnowledgeSource) -> None:
        """Add a source to the knowledge base."""
        if any(s.id == source.id for s in self.sources):
            raise DomainError("Source already exists in this knowledge base")
            
        self.sources.append(source)
        self.updated_at = datetime.now()
        
    def remove_source(self, source_id: str) -> None:
        """Remove a source from the knowledge base."""
        source = next((s for s in self.sources if s.id == source_id), None)
        if not source:
            raise DomainError("Source not found in this knowledge base")
            
        self.sources.remove(source)
        self.updated_at = datetime.now()
        
    def can_be_accessed_by(self, user_id: str) -> bool:
        """Check if user can access this knowledge base."""
        return self.owner_id == user_id
```

## Common Patterns

### Repository Pattern

Repositories abstract data access, allowing domain objects to remain persistence-agnostic:

```python
class AssistantRepository:
    def __init__(self, db_session):
        self.db_session = db_session
        
    def get_by_id(self, assistant_id: str) -> Optional[Assistant]:
        """Get assistant by ID."""
        assistant_data = self.db_session.query(AssistantModel).filter_by(id=assistant_id).first()
        if not assistant_data:
            return None
        
        return self._map_to_domain(assistant_data)
        
    def list_by_owner(self, owner_id: str) -> List[Assistant]:
        """List assistants by owner."""
        assistant_data = self.db_session.query(AssistantModel).filter_by(owner_id=owner_id).all()
        return [self._map_to_domain(a) for a in assistant_data]
        
    def save(self, assistant: Assistant) -> Assistant:
        """Save an assistant."""
        assistant_model = self._map_to_model(assistant)
        self.db_session.merge(assistant_model)
        self.db_session.commit()
        return assistant
        
    def delete(self, assistant_id: str) -> None:
        """Delete an assistant."""
        assistant_model = self.db_session.query(AssistantModel).filter_by(id=assistant_id).first()
        if assistant_model:
            self.db_session.delete(assistant_model)
            self.db_session.commit()
            
    def _map_to_domain(self, model: AssistantModel) -> Assistant:
        """Map database model to domain object."""
        return Assistant(
            id=model.id,
            name=model.name,
            description=model.description,
            owner_id=model.owner_id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
        
    def _map_to_model(self, assistant: Assistant) -> AssistantModel:
        """Map domain object to database model."""
        model = AssistantModel(
            id=assistant.id,
            name=assistant.name,
            description=assistant.description,
            owner_id=assistant.owner_id,
            created_at=assistant.created_at,
            updated_at=assistant.updated_at
        )
        return model
```

### Factory Pattern

Factories encapsulate complex object creation logic:

```python
class AssistantFactory:
    @staticmethod
    def create_from_template(template_id: str, name: str, owner_id: str) -> Assistant:
        """Create an assistant from a template."""
        # Implementation...
```

### Specification Pattern

Specifications encapsulate business rules and can be combined:

```python
class AssistantSpecification:
    @staticmethod
    def has_valid_model(assistant: Assistant) -> bool:
        """Check if assistant has a valid model configuration."""
        # Implementation...
        
    @staticmethod
    def has_access_to_knowledge_base(assistant: Assistant, user_id: str) -> bool:
        """Check if user has access to assistant's knowledge base."""
        # Implementation...
```

## Testing Approach

DDD encourages a test-driven approach focusing on behavior:

### Domain Tests

Test core domain logic in isolation:

```python
def test_space_add_member():
    # Arrange
    space = Space(id="123", name="Test Space", owner_id="owner-1")
    
    # Act
    space.add_member("user-1", "member")
    
    # Assert
    assert space.can_access("user-1") is True
    
    # Act & Assert (should raise exception)
    with pytest.raises(DomainError):
        space.add_member("user-1", "member")  # Already a member
```

### Application Tests

Test application services with mocked repositories:

```python
def test_space_service_create_space(mock_space_repo, mock_user_service):
    # Arrange
    mock_user_service.get_user.return_value = User(id="owner-1", name="Owner")
    
    # Act
    space_service = SpaceService(mock_space_repo, mock_user_service)
    space = space_service.create_space(name="Test Space", owner_id="owner-1")
    
    # Assert
    assert space.name == "Test Space"
    assert space.owner_id == "owner-1"
    mock_space_repo.save.assert_called_once()
```

### Integration Tests

Test the whole stack with real dependencies:

```python
def test_create_space_api(client, db_session):
    # Arrange
    user = create_test_user(db_session)
    token = create_auth_token(user)
    
    # Act
    response = client.post(
        "/api/v1/spaces",
        json={"name": "Test Space"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Test Space"
    assert response.json()["owner_id"] == user.id
```

By following these DDD principles in Intric, we create a maintainable, expressive codebase that directly reflects the business domain and is resilient to changes in technical implementations.