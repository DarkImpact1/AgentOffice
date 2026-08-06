import { useRef, useState, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
import { Agent } from '../store'
import * as THREE from 'three'

interface AgentCharacterProps {
  agent: Agent
  deskPosition: [number, number, number]
  bossPosition: [number, number, number]
  onClick: () => void
}

const DIALOGUE_WALKING = [
  "On my way, boss!",
  "Coming right over!",
  "Be there in a sec!",
  "Walking to cabin...",
]

const DIALOGUE_WORKING: Record<string, string[]> = {
  email: [
    "Checking your inbox...",
    "Scanning for tasks...",
    "Found some emails!",
    "Processing messages...",
  ],
  tab_monitor: [
    "Checking platforms...",
    "Scanning Outlier...",
    "Looking at Scale AI...",
    "Checking Remotasks...",
  ],
  freelance_hunter: [
    "Hunting for jobs...",
    "Searching Upwork...",
    "Drafting proposals...",
    "Found some gigs!",
  ],
  status_tracker: [
    "Compiling report...",
    "Crunching numbers...",
    "Analyzing data...",
    "Almost done boss!",
  ],
}

const DIALOGUE_DONE: Record<string, string[]> = {
  email: [
    "Done! Found some tasks.",
    "Inbox checked, boss!",
    "All emails processed!",
  ],
  tab_monitor: [
    "Platforms checked!",
    "Status report ready!",
    "All clear, boss!",
  ],
  freelance_hunter: [
    "Jobs found, boss!",
    "Proposals ready!",
    "Check the panel!",
  ],
  status_tracker: [
    "Report complete!",
    "Here's your summary!",
    "All done, boss!",
  ],
}

function getRandomDialogue(arr: string[]): string {
  return arr[Math.floor(Math.random() * arr.length)]
}

export function AgentCharacter({ agent, deskPosition, bossPosition, onClick }: AgentCharacterProps) {
  const groupRef = useRef<THREE.Group>(null)
  const [position, setPosition] = useState<[number, number, number]>([
    deskPosition[0],
    0.5,
    deskPosition[2] + 1,
  ])
  const [targetPosition, setTargetPosition] = useState<[number, number, number]>(position)
  const [bobOffset, setBobOffset] = useState(0)
  const [showBubble, setShowBubble] = useState(false)
  const [bubbleText, setBubbleText] = useState('')
  const [lookAtBoss, setLookAtBoss] = useState(false)
  const [armSwing, setArmSwing] = useState(0)

  useEffect(() => {
    switch (agent.status) {
      case 'walking':
        setTargetPosition([bossPosition[0], 0.5, bossPosition[2] + 1.5])
        setBubbleText(getRandomDialogue(DIALOGUE_WALKING))
        setShowBubble(true)
        setLookAtBoss(false)
        break
      case 'working':
        setBubbleText(getRandomDialogue(DIALOGUE_WORKING[agent.name] || ["Working..."]))
        setShowBubble(true)
        setLookAtBoss(true)
        break
      case 'reporting':
        setBubbleText(getRandomDialogue(DIALOGUE_DONE[agent.name] || ["Done!"]))
        setShowBubble(true)
        setLookAtBoss(true)
        break
      case 'idle':
        setTargetPosition([deskPosition[0], 0.5, deskPosition[2] + 1])
        setLookAtBoss(false)
        setTimeout(() => setShowBubble(false), 2000)
        break
      case 'error':
        setBubbleText("Oops! Something went wrong...")
        setShowBubble(true)
        break
    }
  }, [agent.status, deskPosition, bossPosition, agent.name])

  useFrame((state, delta) => {
    if (!groupRef.current) return

    const speed = 3
    const dx = targetPosition[0] - position[0]
    const dz = targetPosition[2] - position[2]
    const distance = Math.sqrt(dx * dx + dz * dz)

    if (distance > 0.1) {
      const moveX = (dx / distance) * speed * delta
      const moveZ = (dz / distance) * speed * delta
      setPosition([
        position[0] + moveX,
        position[1],
        position[2] + moveZ,
      ])
      // Walking bob
      const walkBob = Math.sin(state.clock.elapsedTime * 12) * 0.08
      setBobOffset(walkBob)
      // Arm swing
      setArmSwing(Math.sin(state.clock.elapsedTime * 12) * 0.5)
    } else {
      // Idle animation
      if (agent.status === 'working') {
        setBobOffset(Math.sin(state.clock.elapsedTime * 8) * 0.03)
        setArmSwing(Math.sin(state.clock.elapsedTime * 10) * 0.2)
      } else {
        setBobOffset(Math.sin(state.clock.elapsedTime * 2) * 0.02)
        setArmSwing(0)
      }
    }

    groupRef.current.position.set(position[0], position[1] + bobOffset, position[2])

    // Rotation
    if (distance > 0.1) {
      const angle = Math.atan2(dx, dz)
      groupRef.current.rotation.y = THREE.MathUtils.lerp(
        groupRef.current.rotation.y,
        angle,
        0.15
      )
    } else if (lookAtBoss) {
      // Face the boss cabin
      const toBoss = Math.atan2(bossPosition[0] - position[0], bossPosition[2] - position[2])
      groupRef.current.rotation.y = THREE.MathUtils.lerp(
        groupRef.current.rotation.y,
        toBoss,
        0.1
      )
    } else {
      // Face desk (away from center)
      const toDesk = Math.atan2(deskPosition[0], deskPosition[2])
      groupRef.current.rotation.y = THREE.MathUtils.lerp(
        groupRef.current.rotation.y,
        toDesk + Math.PI,
        0.05
      )
    }
  })

  const statusColor = {
    idle: '#10b981',
    walking: '#f59e0b',
    working: '#3b82f6',
    reporting: '#8b5cf6',
    error: '#ef4444',
  }[agent.status]

  const isMoving = agent.status === 'walking' || 
    Math.sqrt((targetPosition[0] - position[0]) ** 2 + (targetPosition[2] - position[2]) ** 2) > 0.1

  return (
    <group ref={groupRef} onClick={onClick}>
      {/* Body */}
      <mesh castShadow position={[0, 0.3, 0]}>
        <capsuleGeometry args={[0.25, 0.4, 8, 16]} />
        <meshStandardMaterial color={agent.color} />
      </mesh>

      {/* Head */}
      <mesh castShadow position={[0, 0.85, 0]}>
        <sphereGeometry args={[0.2, 16, 16]} />
        <meshStandardMaterial color={agent.color} />
      </mesh>

      {/* Eyes */}
      <mesh position={[0.07, 0.9, 0.16]}>
        <sphereGeometry args={[0.045, 8, 8]} />
        <meshBasicMaterial color="white" />
      </mesh>
      <mesh position={[-0.07, 0.9, 0.16]}>
        <sphereGeometry args={[0.045, 8, 8]} />
        <meshBasicMaterial color="white" />
      </mesh>
      {/* Pupils */}
      <mesh position={[0.07, 0.9, 0.19]}>
        <sphereGeometry args={[0.025, 8, 8]} />
        <meshBasicMaterial color="#1a1a2e" />
      </mesh>
      <mesh position={[-0.07, 0.9, 0.19]}>
        <sphereGeometry args={[0.025, 8, 8]} />
        <meshBasicMaterial color="#1a1a2e" />
      </mesh>

      {/* Left arm */}
      <group position={[-0.32, 0.35, 0]} rotation={[armSwing, 0, 0]}>
        <mesh castShadow>
          <capsuleGeometry args={[0.07, 0.25, 4, 8]} />
          <meshStandardMaterial color={agent.color} />
        </mesh>
      </group>

      {/* Right arm */}
      <group position={[0.32, 0.35, 0]} rotation={[-armSwing, 0, 0]}>
        <mesh castShadow>
          <capsuleGeometry args={[0.07, 0.25, 4, 8]} />
          <meshStandardMaterial color={agent.color} />
        </mesh>
      </group>

      {/* Left leg */}
      <group position={[-0.1, -0.1, 0]} rotation={[isMoving ? -armSwing * 0.7 : 0, 0, 0]}>
        <mesh castShadow>
          <capsuleGeometry args={[0.08, 0.2, 4, 8]} />
          <meshStandardMaterial color={agent.color} metalness={0.3} roughness={0.7} />
        </mesh>
      </group>

      {/* Right leg */}
      <group position={[0.1, -0.1, 0]} rotation={[isMoving ? armSwing * 0.7 : 0, 0, 0]}>
        <mesh castShadow>
          <capsuleGeometry args={[0.08, 0.2, 4, 8]} />
          <meshStandardMaterial color={agent.color} metalness={0.3} roughness={0.7} />
        </mesh>
      </group>

      {/* Status glow */}
      <pointLight position={[0, 1.2, 0]} intensity={0.4} color={statusColor} distance={2} />

      {/* Avatar emoji */}
      <Text
        position={[0, 1.2, 0]}
        fontSize={0.2}
        anchorX="center"
        anchorY="middle"
      >
        {agent.avatar}
      </Text>

      {/* Speech bubble */}
      {showBubble && (
        <group position={[0, 1.7, 0]}>
          {/* Bubble background */}
          <mesh>
            <planeGeometry args={[2, 0.6]} />
            <meshBasicMaterial color="#1a1a2e" />
          </mesh>
          {/* Bubble border */}
          <mesh position={[0, 0, -0.01]}>
            <planeGeometry args={[2.08, 0.68]} />
            <meshBasicMaterial color={agent.color} />
          </mesh>
          {/* Text */}
          <Text
            position={[0, 0, 0.01]}
            fontSize={0.14}
            color="#ffffff"
            anchorX="center"
            anchorY="middle"
            maxWidth={1.8}
          >
            {bubbleText}
          </Text>
          {/* Bubble pointer */}
          <mesh position={[0, -0.38, 0]} rotation={[0, 0, Math.PI / 4]}>
            <planeGeometry args={[0.15, 0.15]} />
            <meshBasicMaterial color="#1a1a2e" />
          </mesh>
        </group>
      )}

      {/* Ground indicator */}
      <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.25, 0.35, 16]} />
        <meshBasicMaterial color={statusColor} opacity={0.6} transparent />
      </mesh>

      {/* Click hint when idle */}
      {agent.status === 'idle' && (
        <Text
          position={[0, -0.2, 0.5]}
          fontSize={0.1}
          color="#a0aec0"
          anchorX="center"
        >
          Click to summon
        </Text>
      )}
    </group>
  )
}
