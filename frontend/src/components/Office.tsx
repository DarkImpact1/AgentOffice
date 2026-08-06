import { OrbitControls, Text, RoundedBox } from '@react-three/drei'
import { useStore } from '../store'
import { AgentCharacter } from './AgentCharacter'

interface OfficeProps {
  onAgentClick: (name: string) => void
}

const DESK_POSITIONS: Record<string, [number, number, number]> = {
  email: [-4, 0, -2],
  tab_monitor: [4, 0, -2],
  freelance_hunter: [-4, 0, 4],
  status_tracker: [4, 0, 4],
}

const BOSS_POSITION: [number, number, number] = [0, 0, -6]
const MEETING_POINT: [number, number, number] = [0, 0, -4]

function Floor() {
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
        <planeGeometry args={[24, 20]} />
        <meshStandardMaterial color="#1a1a2e" />
      </mesh>
      {Array.from({ length: 25 }).map((_, i) => (
        <group key={`grid-${i}`}>
          <mesh position={[-12 + i, 0, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[0.02, 20]} />
            <meshBasicMaterial color="#2d3748" opacity={0.5} transparent />
          </mesh>
          <mesh position={[0, 0, -10 + i]} rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[24, 0.02]} />
            <meshBasicMaterial color="#2d3748" opacity={0.5} transparent />
          </mesh>
        </group>
      ))}
    </group>
  )
}

function BossCabin() {
  return (
    <group position={[0, 0, -6]}>
      {/* Cabin walls */}
      <mesh position={[0, 1.5, -2]} castShadow>
        <boxGeometry args={[8, 3, 0.15]} />
        <meshStandardMaterial color="#2d3748" />
      </mesh>
      <mesh position={[-4, 1.5, 0]} castShadow>
        <boxGeometry args={[0.15, 3, 4]} />
        <meshStandardMaterial color="#2d3748" />
      </mesh>
      <mesh position={[4, 1.5, 0]} castShadow>
        <boxGeometry args={[0.15, 3, 4]} />
        <meshStandardMaterial color="#2d3748" />
      </mesh>
      
      {/* Glass panels */}
      <mesh position={[-4, 1.5, 0]}>
        <boxGeometry args={[0.1, 2, 3]} />
        <meshStandardMaterial color="#4c51bf" opacity={0.2} transparent />
      </mesh>
      <mesh position={[4, 1.5, 0]}>
        <boxGeometry args={[0.1, 2, 3]} />
        <meshStandardMaterial color="#4c51bf" opacity={0.2} transparent />
      </mesh>

      {/* Boss desk */}
      <RoundedBox args={[3, 0.12, 1.5]} radius={0.03} position={[0, 0.8, 0]} castShadow>
        <meshStandardMaterial color="#4a5568" />
      </RoundedBox>
      {[[-1.2, 0, -0.5], [1.2, 0, -0.5], [-1.2, 0, 0.5], [1.2, 0, 0.5]].map((legPos, i) => (
        <mesh key={i} position={[legPos[0], 0.4, legPos[2]]} castShadow>
          <boxGeometry args={[0.08, 0.8, 0.08]} />
          <meshStandardMaterial color="#2d3748" />
        </mesh>
      ))}

      {/* Boss monitors */}
      <RoundedBox args={[0.8, 0.5, 0.05]} radius={0.02} position={[-0.5, 1.15, -0.3]} castShadow>
        <meshStandardMaterial color="#1a1a2e" emissive="#4c51bf" emissiveIntensity={0.2} />
      </RoundedBox>
      <RoundedBox args={[0.8, 0.5, 0.05]} radius={0.02} position={[0.5, 1.15, -0.3]} castShadow>
        <meshStandardMaterial color="#1a1a2e" emissive="#4c51bf" emissiveIntensity={0.2} />
      </RoundedBox>

      {/* Boss chair */}
      <mesh position={[0, 0.5, 0.8]} castShadow>
        <boxGeometry args={[0.6, 0.1, 0.6]} />
        <meshStandardMaterial color="#1a1a2e" />
      </mesh>
      <mesh position={[0, 0.9, 1.05]} castShadow>
        <boxGeometry args={[0.6, 0.7, 0.1]} />
        <meshStandardMaterial color="#1a1a2e" />
      </mesh>

      {/* Cabin nameplate */}
      <Text
        position={[0, 2.8, -1.9]}
        fontSize={0.25}
        color="#f59e0b"
        anchorX="center"
      >
        MOHIT DUBEY
      </Text>
      <Text
        position={[0, 2.5, -1.9]}
        fontSize={0.15}
        color="#a0aec0"
        anchorX="center"
      >
        CEO & Boss
      </Text>

      {/* Cabin light */}
      <pointLight position={[0, 2.5, 0]} intensity={0.8} color="#f59e0b" distance={6} />
    </group>
  )
}

function BossCharacter() {
  return (
    <group position={[0, 0.5, -5.2]}>
      {/* Body */}
      <mesh castShadow position={[0, 0.3, 0]}>
        <capsuleGeometry args={[0.28, 0.45, 8, 16]} />
        <meshStandardMaterial color="#1a1a2e" />
      </mesh>
      {/* Head */}
      <mesh castShadow position={[0, 0.9, 0]}>
        <sphereGeometry args={[0.22, 16, 16]} />
        <meshStandardMaterial color="#fbbf24" />
      </mesh>
      {/* Eyes */}
      <mesh position={[0.08, 0.95, 0.18]}>
        <sphereGeometry args={[0.04, 8, 8]} />
        <meshBasicMaterial color="white" />
      </mesh>
      <mesh position={[-0.08, 0.95, 0.18]}>
        <sphereGeometry args={[0.04, 8, 8]} />
        <meshBasicMaterial color="white" />
      </mesh>
      <mesh position={[0.08, 0.95, 0.2]}>
        <sphereGeometry args={[0.02, 8, 8]} />
        <meshBasicMaterial color="#1a1a2e" />
      </mesh>
      <mesh position={[-0.08, 0.95, 0.2]}>
        <sphereGeometry args={[0.02, 8, 8]} />
        <meshBasicMaterial color="#1a1a2e" />
      </mesh>
      {/* Crown/Boss indicator */}
      <Text position={[0, 1.25, 0]} fontSize={0.25} anchorX="center">
        👑
      </Text>
      {/* Glow */}
      <pointLight position={[0, 1, 0.5]} intensity={0.3} color="#fbbf24" distance={2} />
    </group>
  )
}

function Desk({ position, name, color }: { position: [number, number, number]; name: string; color: string }) {
  return (
    <group position={position}>
      <RoundedBox args={[2, 0.1, 1]} radius={0.02} position={[0, 0.75, 0]} castShadow>
        <meshStandardMaterial color="#4a5568" />
      </RoundedBox>
      {[[-0.8, 0, -0.35], [0.8, 0, -0.35], [-0.8, 0, 0.35], [0.8, 0, 0.35]].map((legPos, i) => (
        <mesh key={i} position={[legPos[0], 0.375, legPos[2]]} castShadow>
          <boxGeometry args={[0.1, 0.75, 0.1]} />
          <meshStandardMaterial color="#2d3748" />
        </mesh>
      ))}
      <RoundedBox args={[0.6, 0.4, 0.05]} radius={0.02} position={[0, 1.0, -0.3]} castShadow>
        <meshStandardMaterial color="#1a1a2e" emissive={color} emissiveIntensity={0.1} />
      </RoundedBox>
      <mesh position={[0.5, 0.85, 0.2]} castShadow>
        <boxGeometry args={[0.3, 0.05, 0.2]} />
        <meshStandardMaterial color="#718096" />
      </mesh>
      <Text
        position={[0, 0.05, 0.8]}
        rotation={[-Math.PI / 2, 0, 0]}
        fontSize={0.2}
        color={color}
        anchorX="center"
      >
        {name.replace('_', ' ').toUpperCase()}
      </Text>
    </group>
  )
}

function MeetingArea() {
  return (
    <group position={[0, 0.01, -4]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[1.8, 32]} />
        <meshStandardMaterial color="#4c51bf" opacity={0.15} transparent />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
        <ringGeometry args={[1.6, 1.8, 32]} />
        <meshStandardMaterial color="#f59e0b" opacity={0.5} transparent />
      </mesh>
      <Text position={[0, 0.1, 2]} rotation={[-Math.PI / 2, 0, 0]} fontSize={0.15} color="#a0aec0">
        📍 Report Here
      </Text>
    </group>
  )
}

function Walls() {
  return (
    <group>
      {/* Back wall */}
      <mesh position={[0, 2, -10]} castShadow receiveShadow>
        <boxGeometry args={[24, 4, 0.2]} />
        <meshStandardMaterial color="#0f0f1a" />
      </mesh>
      {/* Left wall */}
      <mesh position={[-12, 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.2, 4, 20]} />
        <meshStandardMaterial color="#0f0f1a" />
      </mesh>
      {/* Right wall */}
      <mesh position={[12, 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.2, 4, 20]} />
        <meshStandardMaterial color="#0f0f1a" />
      </mesh>
      
      {/* Windows on back wall */}
      {[-6, 6].map((x, i) => (
        <mesh key={i} position={[x, 2.5, -9.9]}>
          <boxGeometry args={[3, 1.5, 0.1]} />
          <meshStandardMaterial color="#1e3a5f" opacity={0.4} transparent emissive="#4c51bf" emissiveIntensity={0.1} />
        </mesh>
      ))}

      {/* Company name */}
      <Text
        position={[0, 3.5, -9.8]}
        fontSize={0.5}
        color="#f59e0b"
        anchorX="center"
      >
        AGENT OFFICE
      </Text>
    </group>
  )
}

function Dividers() {
  return (
    <group>
      {/* Divider between left desks */}
      <mesh position={[-4, 0.6, 1]} castShadow>
        <boxGeometry args={[0.05, 1.2, 5]} />
        <meshStandardMaterial color="#2d3748" opacity={0.7} transparent />
      </mesh>
      {/* Divider between right desks */}
      <mesh position={[4, 0.6, 1]} castShadow>
        <boxGeometry args={[0.05, 1.2, 5]} />
        <meshStandardMaterial color="#2d3748" opacity={0.7} transparent />
      </mesh>
    </group>
  )
}

export function Office({ onAgentClick }: OfficeProps) {
  const { agents } = useStore()

  return (
    <>
      <color attach="background" args={['#0a0a12']} />
      <fog attach="fog" args={['#0a0a12', 15, 30]} />
      
      <ambientLight intensity={0.3} />
      <directionalLight
        position={[10, 15, 10]}
        intensity={0.8}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-far={50}
        shadow-camera-left={-15}
        shadow-camera-right={15}
        shadow-camera-top={15}
        shadow-camera-bottom={-15}
      />
      <pointLight position={[0, 8, 0]} intensity={0.4} color="#4c51bf" />
      <pointLight position={[-6, 4, 2]} intensity={0.3} color="#ef4444" />
      <pointLight position={[6, 4, 2]} intensity={0.3} color="#10b981" />

      <Floor />
      <Walls />
      <Dividers />
      <BossCabin />
      <BossCharacter />
      <MeetingArea />

      {agents.map((agent) => {
        const deskPos = DESK_POSITIONS[agent.name] || [0, 0, 0]
        return (
          <group key={agent.name}>
            <Desk position={deskPos} name={agent.name} color={agent.color} />
            <AgentCharacter
              agent={agent}
              deskPosition={deskPos}
              bossPosition={MEETING_POINT}
              onClick={() => onAgentClick(agent.name)}
            />
          </group>
        )
      })}

      <OrbitControls
        enablePan={true}
        minPolarAngle={Math.PI / 6}
        maxPolarAngle={Math.PI / 2.5}
        minDistance={8}
        maxDistance={25}
        target={[0, 0, -2]}
      />
    </>
  )
}

export { MEETING_POINT, BOSS_POSITION }
