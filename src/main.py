import sys
print("\n📁 Текущий рабочий каталог:", sys.path[0])
print("\n🗂️  Пути поиска модулей (первые 5):")
for p in sys.path[:5]:
    print("  ", p)




