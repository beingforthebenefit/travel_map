import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useTripStore } from "../stores/tripStore";
import { StopRow } from "./StopRow";

export function StopList() {
  const { trip, reorderStops } = useTripStore();
  const stops = trip?.stops || [];

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = stops.findIndex((s) => s.id === active.id);
    const newIndex = stops.findIndex((s) => s.id === over.id);
    if (oldIndex === -1 || newIndex === -1) return;

    const newOrder = [...stops];
    const [removed] = newOrder.splice(oldIndex, 1);
    newOrder.splice(newIndex, 0, removed!);
    reorderStops(newOrder.map((s) => s.id));
  };

  if (stops.length === 0) {
    return (
      <div className="p-6 text-center text-sm text-gray-400">
        No stops yet. Add one below.
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={stops.map((s) => s.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {stops.map((stop, i) => (
            <StopRow key={stop.id} stop={stop} index={i} />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}
