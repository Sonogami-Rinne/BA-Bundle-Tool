import typing
from typing import Generic, TypeVar, Optional, Iterable

T = TypeVar('T')


class LinkedList(Generic[T]):
    class LinkedUnit(Generic[T]):
        def __init__(self, target: T):
            self.data = target
            self.next: T = None

    def __init__(self, target: Optional[T]):
        if target:
            head = LinkedList.LinkedUnit(target)
            self.head: Optional[LinkedList.LinkedUnit] = head
            self.tail: Optional[LinkedList.LinkedUnit] = head
        else:
            self.head: Optional[LinkedList.LinkedUnit] = None
            self.tail: Optional[LinkedList.LinkedUnit] = None

    def add(self, target: T):
        new_unit = LinkedList.LinkedUnit(target)
        if self.head is None:
            self.head = new_unit
            self.tail = new_unit
        else:
            self.tail.next = new_unit
            self.tail = new_unit

    def adds(self, iterable: Iterable[T]):
        while data := next(iter(iterable), None):
            self.add(data)


    def remove(self) -> T:
        if self.head:
            unit = self.head
            self.head = self.head.next
            if self.head is None:
                self.tail = None
            return unit.data

    def walk_through(self) -> typing.Iterable[T]:
        """
        遍历并清空列表，忽略新增的node
        :return: yield
        """
        if self.head is None:
            return ()

        cur_tail = self.tail
        while self.head != cur_tail.next:
            yield self.remove()
