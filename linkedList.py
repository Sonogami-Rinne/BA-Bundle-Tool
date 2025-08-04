import typing
from typing import Generic, TypeVar, Optional, Iterable

T = TypeVar('T')


class LinkedList(Generic[T]):
    class LinkedUnit(Generic[T]):
        def __init__(self, target: T, parent_container):
            self.data: T = target
            self.next: Optional[LinkedList.LinkedUnit[T]] = None

    def __init__(self, target: Optional[T] | list[T]):
        self.head: Optional[LinkedList.LinkedUnit[T]] = None
        self.tail: Optional[LinkedList.LinkedUnit[T]] = None
        self.info = None  # 自定义信息写入

        if type(target) is list:
            self.adds(target)
        else:
            self.add(target)

    def add(self, target: T):
        new_unit = LinkedList.LinkedUnit(target, self)
        if self.head is None:
            self.head = new_unit
            self.tail = new_unit
        else:
            self.tail.next = new_unit
            self.tail = new_unit

    def adds(self, iterable: Iterable[T]):
        if iterable and (head := next(datas := iter(iterable), None)):
            head = LinkedList.LinkedUnit(head, self)
            tail = head
            while data := next(datas, None):
                new_node = LinkedList.LinkedUnit(data, self)
                tail.next = new_node
                tail = new_node
            if self.head is None:
                self.head = head
                self.tail = tail
            else:
                self.tail.next = head
                self.tail = tail

    def pop(self) -> Optional[T]:
        if self.head:
            unit = self.head
            self.head = self.head.next
            if self.head is None:
                self.tail = None
            return unit.data
        return None

    def walk_through(self) -> typing.Iterable[T]:
        """
        遍历并清空列表，忽略新增的node.其实就是BFS遍历一层
        :return: yield
        """
        if self.head is None:
            return ()

        cur_tail = self.tail
        while self.head != cur_tail.next:
            yield self.pop()
