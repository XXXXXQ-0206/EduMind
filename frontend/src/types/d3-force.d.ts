declare module "d3-force" {
    export interface SimulationNodeDatum { index?: number; x?: number; y?: number; vx?: number; vy?: number; fx?: number | null; fy?: number | null }
    export interface SimulationLinkDatum<NodeDatum extends SimulationNodeDatum = SimulationNodeDatum> { source: NodeDatum | string | number; target: NodeDatum | string | number }
    export interface Force<NodeDatum extends SimulationNodeDatum = SimulationNodeDatum> {
        initialize(nodes: NodeDatum[], random?: () => number): void
    }
    export interface ManyBodyForce<NodeDatum extends SimulationNodeDatum = SimulationNodeDatum> extends Force<NodeDatum> {
        strength(strength: number): this
    }
    export interface LinkForce<NodeDatum extends SimulationNodeDatum = SimulationNodeDatum> extends Force<NodeDatum> {
        links(links: SimulationLinkDatum<NodeDatum>[]): this
        id(id: (node: NodeDatum) => string): this
        distance(distance: number): this
        strength(strength: number): this
    }
    export interface PositionForce<NodeDatum extends SimulationNodeDatum = SimulationNodeDatum> extends Force<NodeDatum> {
        strength(strength: number): this
    }
    export interface Simulation<NodeDatum extends SimulationNodeDatum> {
        nodes(nodes: NodeDatum[]): this
        force(name: string, force: Force<NodeDatum> | null): this
        alpha(value: number): this
        alphaDecay(value: number): this
        alphaTarget(value: number): this
        on(typ: string, listener: (this: this) => void): this
        restart(): this
        stop(): this
    }
    export function forceSimulation<NodeDatum extends SimulationNodeDatum = SimulationNodeDatum>(nodes?: NodeDatum[]): Simulation<NodeDatum>
    export function forceManyBody<NodeDatum extends SimulationNodeDatum = SimulationNodeDatum>(): ManyBodyForce<NodeDatum>
    export function forceLink<NodeDatum extends SimulationNodeDatum = SimulationNodeDatum>(links?: SimulationLinkDatum<NodeDatum>[]): LinkForce<NodeDatum>
    export function forceCollide<NodeDatum extends SimulationNodeDatum = SimulationNodeDatum>(radius?: number): PositionForce<NodeDatum>
    export function forceRadial<NodeDatum extends SimulationNodeDatum = SimulationNodeDatum>(radius?: number, x?: number, y?: number): PositionForce<NodeDatum>
}
