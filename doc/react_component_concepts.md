# React 컴포넌트(Component) 개념 설명

이 문서는 React의 핵심 개념인 컴포넌트(Component)에 대해 설명합니다.

## 1. React 컴포넌트란?

React에서 **컴포넌트(Component)**는 **"재사용 가능한 독립적인 UI 조각"**을 의미합니다.

웹 페이지 전체를 하나의 큰 레고 작품이라고 상상했을 때, 이 작품을 만드는 데 사용되는 각각의 레고 블록 하나하나가 바로 React의 컴포넌트입니다. 예를 들어, 버튼, 검색창, 사용자 프로필 카드, 댓글 목록 등이 모두 개별 컴포넌트가 될 수 있습니다. 그리고 이런 작은 컴포넌트들을 조립하여 더 큰 컴포넌트(예: 전체 페이지)를 만듭니다.

현재 우리 프로젝트의 `App.tsx` 파일에 있는 `App` 함수 자체가 우리 애플리케이션의 최상위 부모 컴포넌트입니다.

## 2. 다른 개념과의 비교

### 유니티(Unity) 컴포넌트와의 비교

| 구분 | React 컴포넌트 | Unity 컴포넌트 |
| :--- | :--- | :--- |
| **목적** | UI의 **구조(View)와 동작(Logic)을 정의**하는 UI 그 자체. | 게임 오브젝트에 **특정 기능이나 속성을 추가** (예: Rigidbody, Transform). |
| **관계** | 컴포넌트 안에 다른 컴포넌트를 포함시키는 **포함(Containment)** 관계. (예: `Page` 컴포넌트가 `Button` 컴포넌트를 포함) | 게임 오브젝트에 여러 컴포넌트를 **부착(Attachment)**하는 관계. |
| **결과물** | 화면에 렌더링되는 **UI 요소 (HTML DOM)**. | 게임 내에서 특정 **동작이나 물리적 특성**. |

**핵심 차이:** 유니티에서는 빈 `GameObject`에 `Transform`, `Mesh Renderer`, 스크립트 등의 컴포넌트를 "부착"하여 하나의 객체를 완성합니다. 반면, React에서는 `Page` 컴포넌트 안에 `NavigationBar` 컴포넌트와 `Article` 컴포넌트를 "포함"시켜 UI를 조립합니다. 즉, React 컴포넌트는 **UI를 구성하는 부품** 그 자체에 더 가깝습니다.

### 상속(Inheritance) vs 합성(Composition)

전통적인 객체지향 프로그래밍의 상속과 비교했을 때, React는 **상속보다 합성(Composition)을 선호**하는 철학을 가지고 있습니다.

- **상속 방식:** `SpecialButton`이 `BaseButton`의 모든 기능을 물려받아 확장하는 방식입니다. React에서는 이런 패턴을 거의 사용하지 않습니다.
- **합성 방식 (React의 방식):** `Button`이라는 범용적인 컴포넌트를 만들고, **`props`** 라는 속성을 통해 외부에서 값을 전달받아 모습이나 동작을 다르게 만듭니다.

  ```jsx
  // 다양한 props를 받아 다른 모습으로 렌더링되는 Button 컴포넌트
  <Button color="blue" size="large" onClick={handleLogin}>로그인</Button>
  <Button color="gray" size="small" onClick={handleCancel}>취소</Button>
  ```
  이처럼 기능을 물려받는 대신, 범용적인 "부품"을 만들고 그 부품을 조립하거나 외부에서 속성을 주입하는 방식을 사용합니다. 이 방식이 훨씬 유연하고 재사용성이 높기 때문입니다.

## 3. React 컴포넌트의 주요 특징 요약

1.  **독립적:** 각 컴포넌트는 자신만의 로직과 스타일을 가질 수 있습니다.
2.  **재사용 가능:** 하나의 버튼 컴포넌트를 만들어 앱 전체에서 재사용할 수 있습니다.
3.  **상태(State) 관리:** `useState` Hook을 통해 자신만의 데이터를 가질 수 있으며, 이 데이터가 변경되면 화면이 자동으로 업데이트(리렌더링)됩니다.
4.  **속성(Props) 전달:** 부모 컴포넌트로부터 데이터를 `props`를 통해 전달받을 수 있습니다.
5.  **라이프사이클(Lifecycle):** 컴포넌트가 생성되고(Mounting), 업데이트되고(Updating), 소멸하는(Unmounting) 생명주기를 가지며, `useEffect` Hook을 통해 각 시점에 원하는 작업을 수행할 수 있습니다.

---

## 4. React Hooks 심층 분석

React Hooks는 함수형 컴포넌트에서 상태(State)나 생명주기(Lifecycle)와 같은 React의 핵심 기능들을 "연결(hook into)"할 수 있게 해주는 특별한 함수들입니다.

### `useState`: 상태 관리의 시작

`useState`는 컴포넌트가 기억해야 할 값을 관리하는 데 사용됩니다.

```javascript
const [files, setFiles] = useState<FileItem[]>([]);
```

- **`useState`**: 함수형 컴포넌트 내부에 '상태'를 추가하는 Hook입니다. 일반 변수와 달리, 이 상태가 변경되면 React는 컴포넌트를 자동으로 다시 렌더링(re-rendering)하여 화면을 업데이트합니다.
- **`[files, setFiles]`**: `useState`가 반환하는 배열을 **구조 분해 할당**하는 문법입니다.
  - `files`: 현재 상태 값을 담고 있는 변수입니다. (읽기 전용)
  - `setFiles`: 이 상태 값을 변경할 때 사용하는 함수입니다. 이 함수를 통해서만 상태를 업데이트해야 React가 변화를 감지할 수 있습니다.
- **`<FileItem[]>`**: TypeScript를 사용하여 `files` 변수가 `FileItem` 객체로 이루어진 배열 타입임을 명시합니다.
- **`([])`**: `useState`에 전달하는 인자로, 상태의 **초기값**을 의미합니다. 여기서는 빈 배열로 시작합니다.

### `useEffect`: 생명주기와 사이드 이펙트 관리

`useEffect`는 컴포넌트의 렌더링 결과가 화면에 반영된 이후에 부수적인 효과(Side Effect, 예: API 호출, DOM 조작 등)를 수행하기 위해 사용됩니다.

#### React Hooks와 Unity 이벤트 함수 비교

`useEffect`는 Unity의 `Start`, `Update`와 같은 이벤트 함수와 유사한 점이 많습니다.

- **유사점**: 개발자가 직접 호출하는 것이 아니라, 특정 시점(컴포넌트 렌더링 후)에 프레임워크가 알아서 호출해주는 함수입니다.
  - `useEffect(() => { ... }, [])`는 컴포넌트가 처음 생성될 때 **단 한 번** 실행되므로 Unity의 `Start()`와 비슷합니다.
  - `useEffect(() => { ... }, [someValue])`는 `someValue`가 바뀔 때마다 실행되므로, Unity의 `Update()` 내에서 `if`문으로 값의 변화를 감지하는 것과 유사합니다.
- **차이점**: Unity 이벤트 함수가 스크립트 전체의 생명주기에 초점을 맞춘다면, React Hook은 **특정 상태와 로직을 서로 연결**하는 데 더 집중합니다. 이를 통해 하나의 컴포넌트 내에서 여러 `useEffect`를 사용하여 관심사가 같은 코드끼리 묶어 관리할 수 있습니다.

#### `useEffect`의 Effect 함수 상세 분석

`App.tsx`의 `useEffect`는 `currentPath`가 변경될 때마다 파일 목록을 가져오는 역할을 합니다.

```javascript
useEffect(() => {
  const fetchFiles = async () => {
    try {
      // ... API 요청 로직 ...
      const data = await response.json();
      setFiles(data.items); // 1. 상태 업데이트
    } catch (err) {
      setError(err.message); // 2. 에러 상태 업데이트
    }
  };

  fetchFiles();
}, [currentPath]); // 3. 의존성 배열
```

1.  **상태 업데이트 (`setFiles`)**: API 요청이 성공하면 `setFiles` 함수를 호출하여 `files` 상태를 새로운 데이터로 변경합니다. 이 호출이 React에게 **리렌더링이 필요함**을 알리는 신호입니다.
2.  **에러 상태 업데이트 (`setError`)**: API 요청이 실패하면 `setError` 함수를 호출하여 에러 메시지를 상태에 저장합니다. 이 또한 리렌더링을 유발하여 화면에 에러 메시지를 표시하게 합니다.
3.  **의존성 배열 (`[currentPath]`)**: 이 배열 안에 있는 값(`currentPath`)이 변경될 때만 Effect 함수가 다시 실행됩니다. 만약 이 배열이 비어있다면(`[]`), Effect는 컴포넌트가 처음 마운트될 때 한 번만 실행됩니다.

---

## 5. 비동기 처리: `Promise`와 `async/await`

### `Promise`와 `yield` (Generator) 비교

`async/await` 문법의 기반이 되는 `Promise`는 제너레이터의 `yield`와 유사한 점이 많습니다.

- **유사점**: 둘 다 코드의 실행을 특정 지점에서 **멈추고**, 나중에 이어서 실행할 수 있게 해줍니다. 이 덕분에 비동기 코드를 순차적인 흐름으로 작성할 수 있습니다.
- **차이점**:
  - **`yield`**: **반복(Iteration)**을 위해 값의 스트림을 순차적으로 생성하는 것이 주 목적입니다.
  - **`Promise`**: **하나의 비동기 작업**이 미래에 완료되었을 때의 결과(성공 또는 실패)를 표현하는 것이 주 목적입니다.

결론적으로, `async/await`는 `Promise`라는 비동기 작업 결과물을 `yield`처럼 기다릴 수 있게 하여, 제너레이터의 동작 방식을 비동기 처리에 특화시킨 문법이라고 이해할 수 있습니다.
